import os
import psycopg2
from google import genai
from google.genai import types

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

conn = psycopg2.connect(
    dbname=os.getenv("POSTGRES_DB", "bayyinah_db"),
    user=os.getenv("POSTGRES_USER", "bayyinah_user"),
    password=os.getenv("POSTGRES_PASSWORD", "bayyinah_secure_pass"),
    host=os.getenv("POSTGRES_HOST", "db"),
    port=os.getenv("POSTGRES_PORT", "5432")
)
cursor = conn.cursor()

cursor.execute("SELECT id, clean_text FROM hadiths WHERE embedding IS NULL;")
rows = cursor.fetchall()

print(f"جاري توليد التضمينات لـ {len(rows)} متون...")

for hadith_id, text in rows:
    # استخدام gemini-embedding-001 أو تحديد البعد ليتوافق مع vector(768)
    response = client.models.embed_content(
        model="models/gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=768)
    )
    embedding = response.embeddings[0].values
    cursor.execute(
        "UPDATE hadiths SET embedding = %s WHERE id = %s;",
        (embedding, hadith_id)
    )

conn.commit()
cursor.close()
conn.close()
print("تم تحديث جميع التضمينات بنجاح.")
