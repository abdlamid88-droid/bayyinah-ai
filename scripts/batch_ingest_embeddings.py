import os
import json
import re
import psycopg2
from google import genai
from google.genai import types

def clean_text(text: str) -> str:
    text = re.sub(r'[\u0617-\u061A\u064B-\u0652]', '', text)
    text = re.sub(r'\u0640', '', text)
    text = re.sub(r'[إأآا]', 'ا', text)
    text = re.sub(r'ى', 'ي', text)
    text = re.sub(r'ة', 'ه', text)
    return re.sub(r'\s+', ' ', text).strip()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY is not set.")

client = genai.Client(api_key=api_key)

conn = psycopg2.connect(
    dbname=os.getenv("POSTGRES_DB", "bayyinah_db"),
    user=os.getenv("POSTGRES_USER", "bayyinah_user"),
    password=os.getenv("POSTGRES_PASSWORD", "bayyinah_secure_pass"),
    host=os.getenv("POSTGRES_HOST", "db"),
    port=os.getenv("POSTGRES_PORT", "5432")
)
cursor = conn.cursor()

with open("/app/data/sample_hadiths.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"[*] جاري معالجة وإدراج {len(data)} أحاديث...")

upsert_sql = """
INSERT INTO hadiths (hadith_id, source_book, chapter, hadith_number, raw_text, clean_text, grade, scholar_verdict)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (hadith_id) DO UPDATE SET
    source_book = EXCLUDED.source_book,
    chapter = EXCLUDED.chapter,
    hadith_number = EXCLUDED.hadith_number,
    raw_text = EXCLUDED.raw_text,
    clean_text = EXCLUDED.clean_text,
    grade = EXCLUDED.grade,
    scholar_verdict = EXCLUDED.scholar_verdict;
"""

for item in data:
    cleaned = clean_text(item["raw_text"])
    cursor.execute(upsert_sql, (
        item["hadith_id"],
        item["source_book"],
        item["chapter"],
        item["hadith_number"],
        item["raw_text"],
        cleaned,
        item["grade"],
        item["scholar_verdict"]
    ))
conn.commit()
print("[+] تم تحديث النصوص وبيانات الفهرسة في الجدول بنجاح.")

# استرجاع الأحاديث التي تحتاج لتضمين متجهي
cursor.execute("SELECT id, clean_text FROM hadiths WHERE embedding IS NULL;")
pending_rows = cursor.fetchall()

if not pending_rows:
    print("[+] جميع الأحاديث تحتوي مسبقاً على متجهات دلالية.")
else:
    print(f"[*] جاري توليد المتجهات الدلالية لـ {len(pending_rows)} أحاديث...")
    for row_id, text in pending_rows:
        res = client.models.embed_content(
            model="models/gemini-embedding-001",
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=768)
        )
        vec = res.embeddings[0].values
        cursor.execute("UPDATE hadiths SET embedding = %s WHERE id = %s;", (vec, row_id))

    conn.commit()
    print("[+] تم الانتهاء من توليد وحفظ كافة التضمينات المتجهية بنجاح.")

cursor.close()
conn.close()
