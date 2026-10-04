import logging
from typing import Generator
from sqlmodel import create_engine, Session, SQLModel, text
from app.core.config import settings

logger = logging.getLogger(__name__)

# إنشاء محرك قاعدة البيانات مع pool_pre_ping للتحقق من سلامة الاتصال قبل استخدامه
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)


def init_db() -> None:
    """
    تهيئة قاعدة البيانات:
    1. تفعيل امتداد pgvector للبحث الدلالي بالمتجهات.
    2. إنشاء كافة الجداول المعرفة في النماذج (Models).
    """
    try:
        with Session(engine) as session:
            # تفعيل امتداد المتجهات
            session.exec(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            session.commit()
            logger.info("pgvector extension initialized successfully.")

        # استيراد النماذج للتأكد من تسجيلها في metadata
        from app.models.hadith import HadithRecord  # noqa: F401

        SQLModel.metadata.create_all(engine)
        logger.info("Database tables verified/created successfully.")
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        raise e


def get_session() -> Generator[Session, None, None]:
    """
    مولد جلسات قاعدة البيانات للحقن عبر FastAPI Depends
    """
    with Session(engine) as session:
        yield session
