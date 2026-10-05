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

try:
    from app.services.retrieval import retrieve_candidate_hadiths
    from app.services.arbiter import arbitrate_multi_tier, REFUSAL_MESSAGE
except ImportError:
    from backend.app.services.retrieval import retrieve_candidate_hadiths
    from backend.app.services.arbiter import arbitrate_multi_tier, REFUSAL_MESSAGE

app = FastAPI(title="Bayyinah Engine API", version="0.4.0")

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

_WORKING_EMBED_MODEL = "models/gemini-embedding-001"

@lru_cache(maxsize=2048)
def get_query_embedding(cleaned_text: str):
    global _WORKING_EMBED_MODEL
    if not client:
        return None
    preferred_model = _WORKING_EMBED_MODEL or os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")
    try:
        if "gemini" in preferred_model:
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

class VerifyRequest(BaseModel):
    query: str | None = None
    text: str | None = None

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.4.0"}

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

        # 1. Fast In-Memory Arabic-Aware Cache Lookup (< 5ms)
        cached_result = verification_cache.get(raw_query)
        if cached_result is not None:
            res = dict(cached_result)
            res["cached"] = True
            res["latency_ms"] = round((time.perf_counter() - t0) * 1000, 2)
            return res

        # 2. توليد التضمين الشعاعي للاستعلام
        query_vector = None
        if client:
            try:
                vec_tuple = get_query_embedding(cleaned)
                if vec_tuple:
                    query_vector = list(vec_tuple)
            except Exception as e:
                print(f"[!] Embedding error: {e}", flush=True)

        # 3. استرجاع الشواهد المرشحة بعتبة threshold = 0.58
        candidates = retrieve_candidate_hadiths(
            cleaned_query=cleaned,
            query_vector=query_vector,
            db_pool=db_pool,
            similarity_threshold=0.58,
            limit=8
        )

        # 4. التحكيم الدلالي والحديثي متعدد المستويات (Multi-Tier Verification)
        arb_result = arbitrate_multi_tier(
            client=client,
            raw_query=raw_query,
            cleaned_query=cleaned,
            candidates=candidates
        )

        status_flag = arb_result["verification_status"]
        decision_level = arb_result["decision_level"]
        confidence_score = arb_result["confidence_score"]

        # بناء بطاقة الشاهد المعتمدة (Evidence Card) إن لم تكن الحالة امتناعاً
        evidence_card = None
        if status_flag != "ABSTAIN" and candidates:
            anchor_id = arb_result.get("anchor_hadith_id")
            chosen = next((c for c in candidates if c.get("hadith_id") == anchor_id), candidates[0])
            evidence_card = {
                "hadith_id": chosen.get("hadith_id"),
                "text": chosen.get("raw_text"),
                "source_book": chosen.get("source_book"),
                "source": chosen.get("source_book"),
                "chapter": chosen.get("chapter"),
                "number": chosen.get("hadith_number"),
                "hadith_number": chosen.get("hadith_number"),
                "grade": chosen.get("grade"),
                "verdict": chosen.get("scholar_verdict"),
                "scholar_verdict": chosen.get("scholar_verdict"),
                "semantic_similarity": chosen.get("semantic_similarity", confidence_score)
            }

        alignment_insight = None
        if status_flag != "ABSTAIN":
            alignment_insight = {
                "matched_concepts": arb_result.get("matched_concepts", ["المطابقة الدلالية"]),
                "explanation": arb_result.get("rationale", "")
            }

        # تحديد رسالة الحالة
        if status_flag == "EXACT_MATCH":
            message = "ثابت ومطابق بلفظه في الصحيحين"
            engine_status = "verified"
        elif status_flag == "SEMANTIC_APPROVED":
            message = "المعنى صحيح ومستفاد من حديث معتمد (صياغة بالمعنى)"
            engine_status = "verified"
        else:
            message = REFUSAL_MESSAGE
            engine_status = "refused"

        response_data = {
            "verification_status": status_flag,
            "decision_level": decision_level,
            "confidence_score": confidence_score,
            "similarity_score": confidence_score,
            "semantic_anchor": arb_result.get("semantic_anchor", ""),
            "anchor_hadith_id": arb_result.get("anchor_hadith_id"),
            "rationale": arb_result.get("rationale", ""),
            "guidance": arb_result.get("guidance", ""),
            "status": engine_status,
            "message": message,
            "evidence_card": evidence_card,
            "alignment_insight": alignment_insight,
            "cached": False,
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2)
        }

        # تخزين النتيجة في الكاش السريع
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
