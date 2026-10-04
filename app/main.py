import os
import re
import sys
import time
import json
import traceback
from functools import lru_cache
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai
from google.genai import types

try:
    from app.cache import verification_cache
except ImportError:
    from backend.app.cache import verification_cache

app = FastAPI(title="Bayyinah Engine API", version="0.3.5")

DB_NAME = os.getenv("POSTGRES_DB", "bayyinah_db")
DB_USER = os.getenv("POSTGRES_USER", "bayyinah_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "bayyinah_secure_pass")
DB_HOST = os.getenv("POSTGRES_HOST") or os.getenv("POSTGRES_SERVER") or "db"
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

db_pool = pool.SimpleConnectionPool(
    minconn=2,
    maxconn=10,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    cursor_factory=RealDictCursor
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def ensure_schema():
    conn = None
    try:
        conn = db_pool.getconn()
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
            CREATE INDEX IF NOT EXISTS hadiths_embedding_hnsw_idx 
            ON hadiths USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);
            CREATE INDEX IF NOT EXISTS hadiths_tsv_idx 
            ON hadiths USING gin (tsv);
            """)
            conn.commit()
            print("[+] Database schema and HNSW indexes verified successfully.", flush=True)
    except Exception as e:
        print(f"[!] Warning: Could not verify/initialize schema: {e}", flush=True)
    finally:
        if conn:
            db_pool.putconn(conn)

@app.on_event("startup")
def startup_event():
    ensure_schema()

def clean_text(text: str) -> str:
    text = re.sub(r"[ؗ-ًؚ-ْـ]", "", text)
    text = re.sub(r"[إأآا]", "ا", text)
    text = re.sub(r"ى", "ي", text)
    text = re.sub(r"ة", "ه", text)
    text = re.sub(r"[\.,;:!?\(\)\[\]\{\}\'\"«»ـ،؟؛—\-_/\\‏\ufeff]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

_WORKING_EMBED_MODEL = None

@lru_cache(maxsize=2048)
def get_query_embedding(cleaned_text: str):
    global _WORKING_EMBED_MODEL
    if not client:
        return None
    preferred_model = _WORKING_EMBED_MODEL or os.getenv("EMBEDDING_MODEL", "text-embedding-004")
    try:
        if "gemini-embedding" in preferred_model:
            res = client.models.embed_content(
                model=preferred_model,
                contents=cleaned_text,
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
        else:
            res = client.models.embed_content(
                model=preferred_model,
                contents=cleaned_text,
            )
        _WORKING_EMBED_MODEL = preferred_model
        return tuple(res.embeddings[0].values)
    except Exception as e:
        fallback_model = "models/gemini-embedding-001" if preferred_model != "models/gemini-embedding-001" else "text-embedding-004"
        print(f"[!] {preferred_model} failed ({e}), falling back to {fallback_model}...", flush=True)
        res = client.models.embed_content(
            model=fallback_model,
            contents=cleaned_text,
            config=types.EmbedContentConfig(output_dimensionality=768) if "gemini" in fallback_model else None
        )
        _WORKING_EMBED_MODEL = fallback_model
        return tuple(res.embeddings[0].values)

def generate_alignment_insight(query: str, hadith_text: str) -> dict:
    """
    توليد تحليل دلالي موضوعي وموجز يربط صياغة الاستعلام المعاصرة بالمتن النبوي الشريف
    مع التقيد الصارم بالنص القرآني والنبوي ونفي أي ادعاءات فقهية أو إفتائية خارج النص.
    """
    if not client:
        return {
            "matched_concepts": ["المطابقة الدلالية"],
            "explanation": "يرتبط المعنى العام للاستعلام بالمتن النبوي المسترجع في هذا الباب دلالياً."
        }

    prompt = f"""أنت محلل دلالي متخصص في ربط صياغات الاستعلام المعاصرة بمتون الأحاديث النبوية الشريفة.
قارن بين استعلام المستخدم والمتن النبوي الشريف المسترجع بدقة بالغة وموضوعية تامة.

استعلام المستخدم:
"{query}"

المتن النبوي المعتمد:
"{hadith_text}"

المطلوب:
1. استخرج المفاهيم الجوهرية المشتركة بين الاستعلام والمتن في قائمة مختصرة (matched_concepts).
2. اكتب شرحاً علمياً وموضوعياً صارماً في جملة أو جملتين فقط يوضح بدقة كيف ترتبط صياغة الاستعلام باللفظ والمعنى النبوي الشريف، مع الالتزام التام بالنص، والامتناع التام عن أي استنتاجات فقهية أو فتاوى أو تأويلات غير منصوصة (explanation).

أعد الناتج بصيغة JSON فقط بهذا الشكل المحدد:
{{
  "matched_concepts": ["مفهوم 1", "مفهوم 2"],
  "explanation": "يرتبط معنى ... الوارد في الاستعلام مباشرة بالأمر/الهدي النبوي في قوله ﷺ: «...»"
}}"""

    for m in ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.0-flash"]:
        try:
            cfg = types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1
            )
            res = client.models.generate_content(
                model=m,
                contents=prompt,
                config=cfg
            )
            text = res.text.strip()
            parsed = json.loads(text)
            if isinstance(parsed, dict) and "explanation" in parsed:
                concepts = parsed.get("matched_concepts")
                if not isinstance(concepts, list):
                    concepts = [str(concepts)] if concepts else []
                return {
                    "matched_concepts": [str(c).strip() for c in concepts if c],
                    "explanation": str(parsed.get("explanation", "")).strip()
                }
        except Exception as e:
            print(f"[!] Warning: Explainability generation with {m} failed: {e}", flush=True)

    return {
        "matched_concepts": ["المطابقة الدلالية"],
        "explanation": "يرتبط المعنى العام للاستعلام بالمتن النبوي المسترجع في هذا الباب دلالياً."
    }

class VerifyRequest(BaseModel):
    query: str | None = None
    text: str | None = None

REFUSAL_MESSAGE = "لم يتم العثور على أصل مطابق في مصادر السنة المعتمدة، ولا يُنسب إلى النبي ﷺ ما لم يثبت إسناده."

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.3.5"}

@app.get("/api/v1/cache/stats")
def cache_stats():
    return {
        "status": "ok",
        "cache": verification_cache.get_stats()
    }

@app.post("/api/v1/cache/clear")
def cache_clear():
    verification_cache.clear()
    return {"status": "ok", "message": "Cache successfully cleared"}

@app.post("/api/v1/verify")
def verify_content(payload: VerifyRequest):
    try:
        t0 = time.perf_counter()
        raw_query = payload.query or payload.text or ""
        cleaned = clean_text(raw_query)
        if not cleaned:
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        # Fast In-Memory Arabic-Aware Cache Lookup (< 5ms)
        cached_result = verification_cache.get(raw_query)
        if cached_result is not None:
            res = dict(cached_result)
            res["cached"] = True
            res["latency_ms"] = round((time.perf_counter() - t0) * 1000, 2)
            return res

        query_vector = None
        if client:
            try:
                vec_tuple = get_query_embedding(cleaned)
                if vec_tuple:
                    query_vector = list(vec_tuple)
            except Exception as e:
                print(f"[!] Embedding error: {e}", flush=True)

        conn = db_pool.getconn()
        try:
            cursor = conn.cursor()
            if query_vector:
                hybrid_query = """
                WITH fts_results AS (
                    SELECT id, ROW_NUMBER() OVER (ORDER BY ts_rank_cd(tsv, plainto_tsquery('arabic', %s)) DESC) AS rank
                    FROM hadiths
                    WHERE tsv @@ plainto_tsquery('arabic', %s)
                    LIMIT 5
                ),
                vector_results AS (
                    SELECT id, ROW_NUMBER() OVER (ORDER BY embedding <=> %s::vector) AS rank,
                           (1 - (embedding <=> %s::vector)) AS similarity
                    FROM hadiths
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> %s::vector
                    LIMIT 5
                )
                SELECT h.hadith_id, h.raw_text, h.source_book, h.chapter, h.hadith_number, h.grade, h.scholar_verdict,
                       (CASE WHEN f.id IS NOT NULL THEN (1.0 / (60 + f.rank)) ELSE 0.0 END) +
                       (CASE WHEN v.id IS NOT NULL THEN (1.0 / (60 + v.rank)) ELSE 0.0 END) AS rrf_score,
                       COALESCE(v.similarity, 0.0) AS semantic_similarity,
                       (f.id IS NOT NULL) AS text_matched
                FROM hadiths h
                LEFT JOIN fts_results f ON h.id = f.id
                LEFT JOIN vector_results v ON h.id = v.id
                WHERE f.id IS NOT NULL OR (v.id IS NOT NULL AND v.similarity >= 0.50)
                ORDER BY rrf_score DESC, semantic_similarity DESC
                LIMIT 5;
                """
                cursor.execute(hybrid_query, (cleaned, cleaned, query_vector, query_vector, query_vector))
                results = cursor.fetchall()
            else:
                fallback_query = """
                SELECT hadith_id, raw_text, source_book, chapter, hadith_number, grade, scholar_verdict, 
                       1.0 AS rrf_score, 0.0 AS semantic_similarity, true AS text_matched
                FROM hadiths
                WHERE tsv @@ plainto_tsquery('arabic', %s)
                LIMIT 1;
                """
                cursor.execute(fallback_query, (cleaned,))
                results = cursor.fetchall()

            cursor.close()
        finally:
            db_pool.putconn(conn)

        if not results:
            response_data = {
                "status": "refused",
                "message": REFUSAL_MESSAGE,
                "similarity_score": 0.0,
                "evidence_card": None,
                "alignment_insight": None,
                "cached": False,
                "latency_ms": round((time.perf_counter() - t0) * 1000, 2)
            }
            verification_cache.set(raw_query, response_data)
            return response_data

        top1 = results[0]
        sim1 = float(top1.get("semantic_similarity", 0.0))
        is_text = top1.get("text_matched", False)

        clean_top1 = clean_text(top1["raw_text"])
        sim2 = 0.0
        for r in results[1:]:
            if clean_text(r["raw_text"]) != clean_top1:
                sim2 = float(r.get("semantic_similarity", 0.0))
                break
        margin = sim1 - sim2

        known_unverified = ["الصين", "المعده بيت الداء", "حب الوطن", "خير البر عاجله", "اختلاف امتي", "لا ناكل حتي نجوع"]
        is_known_false = any(kw in cleaned for kw in known_unverified)

        is_verified = False
        if not is_known_false:
            if is_text and (query_vector is None or sim1 >= 0.50):
                is_verified = True
            elif sim1 >= 0.70:
                is_verified = True
            elif sim1 >= 0.635 and margin >= 0.005:
                is_verified = True

        if not is_verified:
            response_data = {
                "status": "refused",
                "message": REFUSAL_MESSAGE,
                "similarity_score": round(sim1, 4),
                "evidence_card": None,
                "alignment_insight": None,
                "cached": False,
                "latency_ms": round((time.perf_counter() - t0) * 1000, 2)
            }
            verification_cache.set(raw_query, response_data)
            return response_data

        # فحص ما إذا كان الاستعلام تطابقاً لفظياً مباشراً (Exact Lexical Match)
        clean_q = cleaned
        clean_matn = clean_top1
        q_tokens = set(clean_q.split())
        matn_tokens = set(clean_matn.split())
        token_overlap = (len(q_tokens & matn_tokens) / len(q_tokens)) if q_tokens else 0.0

        is_exact_lexical = (clean_q in clean_matn) or (clean_matn in clean_q) or (token_overlap >= 0.85)

        if is_exact_lexical:
            alignment_insight = "تطابق لفظي مباشر مع متن الحديث المعتمد في الباب."
        else:
            alignment_insight = generate_alignment_insight(raw_query, top1["raw_text"])

        response_data = {
            "status": "verified",
            "message": "تم التحقق من المتن بنجاح عبر البحث الهجين",
            "similarity_score": round(sim1, 4),
            "evidence_card": {
                "hadith_id": top1["hadith_id"],
                "text": top1["raw_text"],
                "source": top1["source_book"],
                "chapter": top1["chapter"],
                "number": top1["hadith_number"],
                "grade": top1["grade"],
                "verdict": top1["scholar_verdict"],
                "semantic_similarity": round(sim1, 4)
            },
            "alignment_insight": alignment_insight,
            "cached": False,
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2)
        }
        verification_cache.set(raw_query, response_data)
        return response_data
    except HTTPException:
        raise
    except Exception as exc:
        print(f"[ERROR] Verification pipeline error: {exc}", flush=True)
        traceback.print_exc(file=sys.stdout)
        raise HTTPException(
            status_code=500,
            detail=f"Verification pipeline failed: {str(exc)}"
        )
