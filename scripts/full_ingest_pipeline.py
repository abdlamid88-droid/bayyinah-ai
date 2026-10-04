import os
import re
import sys
import time
import glob
import json
import csv
import psycopg2
from psycopg2.extras import execute_values
from google import genai
from google.genai import types

def clean_arabic_text(text: str) -> str:
    """إزالة علامات التشكيل والتطويل وتوحيد الهمزات والحروف للبحث الدلالي والمعجمي."""
    if not text:
        return ""
    # إزالة التشكيل (الفتحة، الضمة، الكسرة، السكون، الشدة، التنوين)
    text = re.sub(r'[\u0617-\u061A\u064B-\u0652]', '', text)
    # إزالة التطويل (الكشيدة)
    text = re.sub(r'\u0640', '', text)
    # توحيد الهمزات والألف
    text = re.sub(r'[إأآا]', 'ا', text)
    # توحيد الياء والألف المقصورة
    text = re.sub(r'ى', 'ي', text)
    # توحيد التاء المربوطة والهاء
    text = re.sub(r'ة', 'ه', text)
    # إزالة المسافات الزائدة
    return re.sub(r'\s+', ' ', text).strip()

def detect_and_parse_datasets(data_dir: str = "data") -> list[dict]:
    """
    اكتشاف جميع ملفات البيانات بمختلف الصيغ الممكنة:
    (.json, .jsonl, .csv, .parquet, .sqlite, .db)
    واستخراج الحقول المعيارية مع إزالة التكرار.
    """
    print(f"[*] فحص واكتشاف مصادر البيانات في: '{data_dir}'...")
    all_files = []
    for root, _, files in os.walk(data_dir):
        for fname in sorted(files):
            fpath = os.path.join(root, fname)
            ext = os.path.splitext(fname)[1].lower()
            if ext in [".json", ".jsonl", ".csv", ".parquet", ".sqlite", ".db"]:
                all_files.append((fpath, ext))

    print(f"[+] تم العثور على {len(all_files)} ملفات بيانات: {[f[0] for f in all_files]}")

    extracted_records = []
    for fpath, ext in all_files:
        raw_items = []
        try:
            if ext == ".json":
                with open(fpath, "r", encoding="utf-8") as fp:
                    content = json.load(fp)
                    if isinstance(content, list):
                        raw_items = content
                    elif isinstance(content, dict):
                        raw_items = content.get("data") or content.get("hadiths") or [content]
            elif ext == ".jsonl":
                with open(fpath, "r", encoding="utf-8") as fp:
                    for line in fp:
                        line = line.strip()
                        if line:
                            raw_items.append(json.loads(line))
            elif ext == ".csv":
                with open(fpath, "r", encoding="utf-8") as fp:
                    reader = csv.DictReader(fp)
                    raw_items = list(reader)
            elif ext == ".parquet":
                try:
                    import pandas as pd
                    df = pd.read_parquet(fpath)
                    raw_items = df.to_dict(orient="records")
                except Exception as pe:
                    print(f"[!] تعذر قراءة Parquet ({pe})، يرجى التأكد من توفر pandas/pyarrow.")
            elif ext in [".sqlite", ".db"]:
                import sqlite3
                conn_sq = sqlite3.connect(fpath)
                conn_sq.row_factory = sqlite3.Row
                cur_sq = conn_sq.cursor()
                cur_sq.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cur_sq.fetchall()
                for tbl in tables:
                    tname = tbl[0]
                    cur_sq.execute(f"SELECT * FROM {tname};")
                    rows = cur_sq.fetchall()
                    raw_items.extend([dict(r) for r in rows])
                conn_sq.close()

            print(f"  - تم استخراج {len(raw_items)} سجل أولي من '{fpath}'")

            for item in raw_items:
                raw_text = (
                    item.get("text")
                    or item.get("raw_text")
                    or item.get("matn")
                    or item.get("content")
                    or ""
                ).strip()

                if not raw_text or len(raw_text) < 5:
                    continue

                cleaned_text = (
                    item.get("cleaned_text")
                    or item.get("clean_text")
                    or clean_arabic_text(raw_text)
                ).strip()

                source_book = (
                    item.get("source_book")
                    or item.get("source")
                    or item.get("book")
                    or "صحيح البخاري"
                ).strip()

                chapter = (
                    item.get("chapter")
                    or item.get("bab")
                    or item.get("kitab")
                    or ""
                ).strip()

                hadith_num = str(
                    item.get("hadith_number")
                    or item.get("number")
                    or item.get("hadith_id")
                    or ""
                ).strip()

                scholar_verdict = (
                    item.get("scholar_verdict")
                    or item.get("grade")
                    or item.get("verdict")
                    or "صحيح"
                ).strip()

                hadith_id = str(
                    item.get("hadith_id")
                    or f"{source_book}_{hadith_num}"
                ).strip()

                extracted_records.append({
                    "text": raw_text,
                    "cleaned_text": cleaned_text,
                    "source_book": source_book,
                    "chapter": chapter,
                    "hadith_number": hadith_num,
                    "scholar_verdict": scholar_verdict,
                    "hadith_id": hadith_id,
                })
        except Exception as e:
            print(f"[!] خطأ أثناء فحص الملف '{fpath}': {e}")

    # إزالة التكرار بالاعتماد على المتن المنظف (أول 60 حرفاً)
    deduped = {}
    for rec in extracted_records:
        norm_key = clean_arabic_text(rec["cleaned_text"])[:60]
        if norm_key not in deduped:
            deduped[norm_key] = rec
        else:
            # دمج البيانات الأغنى
            existing = deduped[norm_key]
            if len(rec["text"]) > len(existing["text"]):
                existing["text"] = rec["text"]
            if not existing["chapter"] and rec["chapter"]:
                existing["chapter"] = rec["chapter"]
            if not existing["hadith_number"] and rec["hadith_number"]:
                existing["hadith_number"] = rec["hadith_number"]

    final_records = list(deduped.values())
    print(f"[+] إجمالي الأحاديث الفريدة بعد الفحص وإزالة التكرار: {len(final_records)} حديثاً.")
    return final_records

def setup_database_schema(conn):
    """تهيئة امتداد pgvector وجدول hadiths مع فهرس HNSW بالمحددات المطلوبة."""
    print("[*] تنفيذ ترحيل البنية وفهرس HNSW (Schema Migration)...")
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS hadiths (
            id SERIAL PRIMARY KEY,
            text TEXT NOT NULL,
            cleaned_text TEXT NOT NULL,
            source_book VARCHAR(100) DEFAULT 'صحيح البخاري',
            chapter VARCHAR(150),
            hadith_number VARCHAR(50),
            scholar_verdict VARCHAR(50) DEFAULT 'صحيح',
            embedding vector(768),
            hadith_id VARCHAR(50),
            raw_text TEXT GENERATED ALWAYS AS (text) STORED,
            clean_text TEXT GENERATED ALWAYS AS (cleaned_text) STORED,
            grade VARCHAR(50) GENERATED ALWAYS AS (scholar_verdict) STORED,
            tsv tsvector GENERATED ALWAYS AS (to_tsvector('arabic', coalesce(cleaned_text, ''))) STORED
        );
        """)
        cur.execute("""
        CREATE INDEX IF NOT EXISTS hadiths_embedding_hnsw_idx 
        ON hadiths USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
        """)
        cur.execute("""
        CREATE INDEX IF NOT EXISTS hadiths_tsv_idx 
        ON hadiths USING gin (tsv);
        """)
        conn.commit()
    print("[+] تم التحقق من إنشاء الجدول hadiths وفهرس HNSW وفهرس البحث اللفظي بنجاح.")

_WORKING_EMBED_MODEL = None

def get_embedding(client, text: str, model: str = None) -> list[float]:
    """توليد التضمين الدلالي عبر Google GenAI SDK مع حفظ النموذج الناجح تلقائياً لتسريع المعالجة."""
    global _WORKING_EMBED_MODEL

    # استخدام النموذج الذي ثبت نجاحه مسبقاً
    if _WORKING_EMBED_MODEL:
        if _WORKING_EMBED_MODEL == "text-embedding-004":
            res = client.models.embed_content(
                model="text-embedding-004",
                contents=text,
            )
            return res.embeddings[0].values
        else:
            res = client.models.embed_content(
                model=_WORKING_EMBED_MODEL,
                contents=text,
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            return res.embeddings[0].values

    # المحاولة الأولى: text-embedding-004
    try:
        res = client.models.embed_content(
            model=model or "text-embedding-004",
            contents=text,
        )
        _WORKING_EMBED_MODEL = model or "text-embedding-004"
        print(f"  [i] تم تفعيل نموذج التضمين الأساسي: {_WORKING_EMBED_MODEL}")
        return res.embeddings[0].values
    except Exception as e:
        # إذا تعذر، التحول إلى gemini-embedding-001 وضبط الأبعاد على 768
        target_fallback = "models/gemini-embedding-001"
        res = client.models.embed_content(
            model=target_fallback,
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=768)
        )
        _WORKING_EMBED_MODEL = target_fallback
        print(f"  [i] تم تفعيل النموذج البديل المتوافق (768D): {_WORKING_EMBED_MODEL}")
        return res.embeddings[0].values

def ingest_all():
    """خط أنابيب الاستيراد والتوليد الكامل."""
    db_host = os.getenv("POSTGRES_HOST") or os.getenv("POSTGRES_SERVER") or "db"
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "bayyinah_db")
    db_user = os.getenv("POSTGRES_USER", "bayyinah_user")
    db_pass = os.getenv("POSTGRES_PASSWORD", "bayyinah_secure_pass")

    print(f"[*] الاتصال بقاعدة البيانات {db_user}@{db_host}:{db_port}/{db_name}...")
    conn = psycopg2.connect(
        host=db_host,
        port=db_port,
        dbname=db_name,
        user=db_user,
        password=db_pass
    )

    setup_database_schema(conn)

    # قراءة واكتشاف الملفات
    records = detect_and_parse_datasets("data")
    if not records:
        print("[!] لم يتم العثور على أي سجلات في data/.")
        conn.close()
        return

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY غير متوفر في متغيرات البيئة.")

    client = genai.Client(api_key=api_key)

    print(f"[*] بدء توليد المتجهات الدلالية (Embeddings) وإدراج {len(records)} أحاديث بدفعات مرنة...")
    inserted_count = 0
    batch_size = 5

    with conn.cursor() as cur:
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            print(f"  -> معالجة الدفعة {i // batch_size + 1} ({len(batch)} أحاديث)...")
            
            for rec in batch:
                # محاولة فحص ما إذا كان الحديث موجوداً مسبقاً ومضمناً
                cur.execute(
                    "SELECT id, embedding FROM hadiths WHERE cleaned_text = %s LIMIT 1;",
                    (rec["cleaned_text"],)
                )
                existing = cur.fetchone()

                if existing and existing[1] is not None:
                    # الحديث موجود ويحتوي متجهاً
                    continue

                emb = None
                for attempt in range(3):
                    try:
                        emb = get_embedding(client, rec["cleaned_text"], model="text-embedding-004")
                        break
                    except Exception as err:
                        print(f"    [!] محاولة {attempt + 1} فشلت لـ '{rec['hadith_id']}': {err}")
                        time.sleep(1 + attempt * 2)

                if existing:
                    # تحديث المتجه للسجل القائم
                    cur.execute(
                        "UPDATE hadiths SET embedding = %s, text = %s, source_book = %s, chapter = %s, hadith_number = %s, scholar_verdict = %s, hadith_id = %s WHERE id = %s;",
                        (emb, rec["text"], rec["source_book"], rec["chapter"], rec["hadith_number"], rec["scholar_verdict"], rec["hadith_id"], existing[0])
                    )
                else:
                    # إدراج سجل جديد
                    cur.execute(
                        """
                        INSERT INTO hadiths (
                            text, cleaned_text, source_book, chapter, hadith_number, scholar_verdict, hadith_id, embedding
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                        """,
                        (rec["text"], rec["cleaned_text"], rec["source_book"], rec["chapter"], rec["hadith_number"], rec["scholar_verdict"], rec["hadith_id"], emb)
                    )
                inserted_count += 1
            
            conn.commit()
            time.sleep(0.3)  # احترام قيود المعدل Rate-limits

        # التحقق الإحصائي النهائي
        cur.execute("SELECT count(*), count(embedding) FROM hadiths;")
        total_rows, total_embedded = cur.fetchone()
        print("\n" + "=" * 55)
        print("📊 إحصائيات قاعدة البيانات بعد اكتمال الاستيراد:")
        print(f"  - إجمالي السجلات في الجدول: {total_rows}")
        print(f"  - إجمالي السجلات ذات المتجهات (Embeddings): {total_embedded}")
        print("=" * 55)

        # إعادة تحليل الجدول لتحديث إحصائيات المخطط والفهارس
        cur.execute("ANALYZE hadiths;")
        conn.commit()

    conn.close()
    print("[+] اكتملت عملية الاستيراد والتوليد المتجهي بنجاح تام.")

if __name__ == "__main__":
    ingest_all()
