from fastapi import APIRouter, Depends
from sqlmodel import Session, text
from app.db.session import get_session
from app.core.config import settings

router = APIRouter()


@router.get("/health", summary="فحص جاهزية الخادم وقاعدة البيانات")
def health_check(session: Session = Depends(get_session)):
    """
    نقطة فحص الجاهزية (Health Check):
    - فحص حالة الخادم ومحرك بينة AI.
    - فحص الاتصال بقاعدة البيانات PostgreSQL.
    - فحص تفعيل امتداد pgvector.
    """
    db_status = "unknown"
    vector_status = "unknown"

    try:
        # اختبار استعلام بسيط على قاعدة البيانات
        result = session.exec(text("SELECT 1")).first()
        if result and result[0] == 1:
            db_status = "connected"

        # اختبار وجود امتداد pgvector
        ext_check = session.exec(
            text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        ).first()
        if ext_check:
            vector_status = "ready"
        else:
            vector_status = "missing"
    except Exception as e:
        db_status = f"error: {str(e)}"
        vector_status = "unavailable"

    is_overall_healthy = (db_status == "connected") and (vector_status == "ready")

    return {
        "status": "healthy" if is_overall_healthy else "degraded",
        "service": settings.PROJECT_NAME,
        "database": db_status,
        "pgvector": vector_status,
        "embedding_dimension": settings.EMBEDDING_DIMENSION,
    }
