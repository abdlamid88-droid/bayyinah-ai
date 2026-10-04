import json
import os
import psycopg2
from psycopg2.extras import execute_values

# قراءة متغيرات الاتصال من البيئة أو القيم الافتراضية للدوكر
DB_NAME = os.getenv("POSTGRES_DB", "bayyinah_db")
DB_USER = os.getenv("POSTGRES_USER", "bayyinah_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "bayyinah_secure_pass")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5434")

JSONL_PATH = "data/processed/hadiths.jsonl"

def ingest():
    if not os.path.exists(JSONL_PATH):
        print(f"الملف {JSONL_PATH} غير موجود.")
        return

    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cursor = conn.cursor()

    records = []
    with open(JSONL_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                records.append((
                    item.get("hadith_id"),
                    item.get("raw_text"),
                    item.get("clean_text"),
                    item.get("source_book"),
                    item.get("chapter"),
                    item.get("hadith_number"),
                    item.get("grade"),
                    item.get("scholar_verdict")
                ))

    query = """
    INSERT INTO hadiths (
        hadith_id, raw_text, clean_text, source_book, chapter, hadith_number, grade, scholar_verdict
    ) VALUES %s
    ON CONFLICT (hadith_id) DO UPDATE SET
        raw_text = EXCLUDED.raw_text,
        clean_text = EXCLUDED.clean_text,
        source_book = EXCLUDED.source_book,
        chapter = EXCLUDED.chapter,
        hadith_number = EXCLUDED.hadith_number,
        grade = EXCLUDED.grade,
        scholar_verdict = EXCLUDED.scholar_verdict;
    """

    execute_values(cursor, query, records)
    conn.commit()
    cursor.close()
    conn.close()
    print(f"تم إدراج/تحديث {len(records)} سجل بنجاح في قاعدة البيانات.")

if __name__ == "__main__":
    ingest()
