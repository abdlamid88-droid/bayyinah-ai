from typing import Optional, List
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from pgvector.sqlalchemy import Vector
from app.core.config import settings


class HadithRecord(SQLModel, table=True):
    """
    نموذج سجل الحديث والمتن المعتمد في قاعدة البيانات مع دعم متجهات البحث الدلالي
    """
    __tablename__ = "hadith_records"

    # المعرف الرقمي الفريد
    id: Optional[int] = Field(default=None, primary_key=True)

    # اسم الكتاب والمصدر المعتمد (مثل: صحيح البخاري، صحيح مسلم، الدرر السنية)
    source: str = Field(index=True, description="اسم الكتاب والمصدر المعتمد")

    # الباب / الموضوع
    chapter: Optional[str] = Field(default=None, index=True, description="الباب أو الموضوع الفقهي/المعرفي")

    # رقم الحديث في المصدر
    hadith_number: Optional[str] = Field(default=None, index=True, description="رقم الحديث في المصدر المعتمد")

    # المتن الأصلي مشكولاً بالكامل (للعرض النهائي)
    text_raw: str = Field(description="المتن الأصلي مشكولاً بالكامل للعرض النهائي")

    # المتن بعد إزالة التشكيل وتوحيد الحروف (لأغراض البحث الدقيق والهجين)
    text_clean: str = Field(index=True, description="المتن بعد إزالة التشكيل وتوحيد الحروف للبحث")

    # حكم المحدثين ودرجة الصحة (صحيح، حسن، ضعيف، إلخ)
    grade: Optional[str] = Field(default=None, index=True, description="حكم المحدثين ودرجة الصحة")

    # الراوي الأعلى أو السند إن وجد
    narrator: Optional[str] = Field(default=None, description="الراوي الأعلى أو السند إن وجد")

    # حقل متجهات للأبعاد المتوافقة مع نماذج التضمين النصي
    embedding: Optional[List[float]] = Field(
        default=None,
        sa_column=Column(Vector(settings.EMBEDDING_DIMENSION)),
        description="متجهات التضمين الدلالي (Vector Dimension)"
    )
