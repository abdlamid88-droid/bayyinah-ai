"""
خدمة البحث والاسترجاع الدلالي والهجين (Hybrid & Vector Retrieval Service)
محرك بَيّنة AI (Bayyinah Engine)
"""
from psycopg2 import pool
from typing import List, Dict, Any, Optional

def retrieve_candidate_hadiths(
    cleaned_query: str,
    query_vector: Optional[List[float]],
    db_pool: pool.SimpleConnectionPool,
    similarity_threshold: float = 0.58,
    limit: int = 8
) -> List[Dict[str, Any]]:
    """
    استرجاع الشواهد الحديثية المرشحة باستخدام البحث الهجين (FTS + pgvector)
    مع اعتماد عتبة التشابه الدلالي (threshold = 0.58) لتمرير كافة الشواهد المقاربة موضوعياً.
    """
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cursor:
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
                    LIMIT 10
                )
                SELECT h.id, h.hadith_id, h.raw_text, h.source_book, h.chapter, h.hadith_number, h.grade, h.scholar_verdict,
                       (CASE WHEN f.id IS NOT NULL THEN (1.0 / (60 + f.rank)) ELSE 0.0 END) +
                       (CASE WHEN v.id IS NOT NULL THEN (1.0 / (60 + v.rank)) ELSE 0.0 END) AS rrf_score,
                       COALESCE(v.similarity, 0.0) AS semantic_similarity,
                       (f.id IS NOT NULL) AS text_matched
                FROM hadiths h
                LEFT JOIN fts_results f ON h.id = f.id
                LEFT JOIN vector_results v ON h.id = v.id
                WHERE f.id IS NOT NULL OR (v.id IS NOT NULL AND v.similarity >= %s)
                ORDER BY rrf_score DESC, semantic_similarity DESC
                LIMIT %s;
                """
                cursor.execute(hybrid_query, (
                    cleaned_query, cleaned_query, 
                    query_vector, query_vector, query_vector,
                    similarity_threshold, limit
                ))
                rows = cursor.fetchall()
            else:
                fallback_query = """
                SELECT id, hadith_id, raw_text, source_book, chapter, hadith_number, grade, scholar_verdict, 
                       1.0 AS rrf_score, 0.0 AS semantic_similarity, true AS text_matched
                FROM hadiths
                WHERE tsv @@ plainto_tsquery('arabic', %s)
                LIMIT %s;
                """
                cursor.execute(fallback_query, (cleaned_query, limit))
                rows = cursor.fetchall()

            candidates = []
            for r in rows:
                candidates.append({
                    "id": r.get("id"),
                    "hadith_id": r.get("hadith_id"),
                    "raw_text": r.get("raw_text"),
                    "text": r.get("raw_text"),
                    "source_book": r.get("source_book"),
                    "source": r.get("source_book"),
                    "chapter": r.get("chapter"),
                    "hadith_number": r.get("hadith_number"),
                    "number": r.get("hadith_number"),
                    "grade": r.get("grade"),
                    "scholar_verdict": r.get("scholar_verdict"),
                    "verdict": r.get("scholar_verdict"),
                    "semantic_similarity": round(float(r.get("semantic_similarity", 0.0)), 4),
                    "text_matched": bool(r.get("text_matched", False)),
                    "rrf_score": float(r.get("rrf_score", 0.0))
                })
            return candidates
    finally:
        db_pool.putconn(conn)
