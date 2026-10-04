import os
import re
import time
import json
import psycopg2
from psycopg2.extras import execute_values
from google import genai
from google.genai import types

DB_NAME = os.getenv("POSTGRES_DB", "bayyinah_db")
DB_USER = os.getenv("POSTGRES_USER", "bayyinah_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "bayyinah_secure_pass")
DB_HOST = os.getenv("POSTGRES_SERVER", "db")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def clean_arabic_text(text: str) -> str:
    # إزالة التشكيل والتطويل وتوحيد الهمزات والياء/الألف المقصورة
    text = re.sub(r'[\u0617-\u061A\u064B-\u0652]', '', text)
    text = re.sub(r'\u0640', '', text)
    text = re.sub(r'[إأآا]', 'ا', text)
    text = re.sub(r'ى', 'ي', text)
    text = re.sub(r'ة', 'ه', text)
    return re.sub(r'\s+', ' ', text).strip()

def get_batch_embeddings(texts: list[str], batch_size: int = 50) -> list[list[float]]:
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        chunk = texts[i:i + batch_size]
        try:
            # استدعاء التضمين الدفعي
            response = client.models.embed_content(
                model="models/gemini-embedding-001",
                contents=chunk,
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            for emb in response.embeddings:
                all_embeddings.append(emb.values)
        except Exception as e:
            print(f"[!] خطأ في معالجة الدفعة {i // batch_size + 1}: {e}")
            time.sleep(2)
            # إعادة المحاولة في حال وجود تقييد لحظي
            response = client.models.embed_content(
                model="models/gemini-embedding-001",
                contents=chunk,
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            for emb in response.embeddings:
                all_embeddings.append(emb.values)
        time.sleep(0.5)  # مراعاة قيود المعدل (Rate Limiting)
    return all_embeddings

def ingest_hadiths(data_path: str):
    if not os.path.exists(data_path):
        print(f"[x] الملف غير موجود: {data_path}")
        return

    with open(data_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    print(f"[*] تم تحميل {len(records)} حديثاً من الملف.")

    # تحضير النصوص المنظفة
    cleaned_texts = [clean_arabic_text(r["raw_text"]) for r in records]

    print("[*] بدء استخراج المتجهات الدلالية عبر Gemini API...")
    embeddings = get_batch_embeddings(cleaned_texts)

    # تجهيز السجلات للإدراج في قاعدة البيانات
    rows_to_insert = []
    for r, clean_t, emb in zip(records, cleaned_texts, embeddings):
        rows_to_insert.append((
            r["hadith_id"],
            r["source_book"],
            r.get("chapter", ""),
            str(r.get("hadith_number", "")),
            r["raw_text"],
            clean_t,
            r.get("grade", "صحيح"),
            r.get("scholar_verdict", ""),
            emb
        ))

    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )
    cursor = conn.cursor()

    upsert_query = """
    INSERT INTO hadiths (
        hadith_id, source_book, chapter, hadith_number,
        raw_text, clean_text, grade, scholar_verdict, embedding
    ) VALUES %s
    ON CONFLICT (hadith_id) DO UPDATE SET
        clean_text = EXCLUDED.clean_text,
        grade = EXCLUDED.grade,
        scholar_verdict = EXCLUDED.scholar_verdict,
        embedding = EXCLUDED.embedding;
    """

    print("[*] إدراج البيانات داخل PostgreSQL / pgvector...")
    execute_values(cursor, upsert_query, rows_to_insert, template="(%s, %s, %s, %s, %s, %s, %s, %s, %s::vector)")
    conn.commit()

    print("[*] إعادة بناء الفهارس لتحسين سرعة الاستعلام...")
    cursor.execute("REINDEX INDEX hadiths_embedding_idx;")
    cursor.execute("REINDEX INDEX hadiths_tsv_idx;")
    conn.commit()

    cursor.close()
    conn.close()
    print("[+] اكتمل الاستيراد والفهرسة بنجاح.")

if __name__ == "__main__":
    import sys
    file_arg = sys.argv[1] if len(sys.argv) > 1 else "/app/data/bukhari_muslim_batch.json"
    ingest_hadiths(file_arg)
