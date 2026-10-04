from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.evidence import EvidenceCardResponse


class VerificationRequest(BaseModel):
    """
    طلب التحقق المعرفي من نص أو مقولة
    """
    text: str = Field(
        ...,
        min_length=3,
        description="النص المراد التحقق من صحته، نسبته، وشواهده من المصادر المعتمدة"
    )
    confidence_threshold: Optional[float] = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="عتبة الثقة المطلوبة لقبول الدليل"
    )
    limit: Optional[int] = Field(
        default=5,
        ge=1,
        le=20,
        description="الحد الأقصى لعدد بطاقات الأدلة المرجعة"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "text": "إنما الأعمال بالنيات",
                "confidence_threshold": 0.75,
                "limit": 3
            }
        }
    }


class VerificationResponse(BaseModel):
    """
    استجابة التحقق المعرفي الشاملة
    """
    query: str = Field(..., description="النص المدخل في الاستعلام")
    verdict: str = Field(..., description="الحكم العام للتحقق (معتمد وموثق، يحتاج تثبت، ضعيف/غير ثابت، إلخ)")
    total_evidences: int = Field(..., description="عدد الشواهد والأدلة المطابقة")
    evidences: List[EvidenceCardResponse] = Field(default_factory=list, description="قائمة بطاقات الأدلة الموثقة")
