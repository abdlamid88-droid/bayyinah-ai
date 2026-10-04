from typing import Optional
from pydantic import BaseModel, Field


class EvidenceCardResponse(BaseModel):
    """
    بطاقة الدليل الموثقة (Evidence Card)
    تعرض نتائج مطابقة الشاهد من المصادر المعتمدة مع بيان الحكم والدرجة ونسبة الثقة.
    """
    id: Optional[int] = Field(default=None, description="المعرف الرقمي في قاعدة البيانات إن وجد")
    matched_text: str = Field(..., description="نص الشاهد أو المتن الموثق من المصدر")
    source: str = Field(..., description="اسم الكتاب والمصدر المعتمد (مثل: صحيح البخاري)")
    hadith_number: Optional[str] = Field(default=None, description="رقم الحديث في المصدر المعتمد")
    chapter: Optional[str] = Field(default=None, description="الباب أو الموضوع المعرفي")
    grade: Optional[str] = Field(default=None, description="حكم المحدثين ودرجة الصحة (صحيح، حسن، إلخ)")
    narrator: Optional[str] = Field(default=None, description="الراوي الأعلى أو السند")
    confidence_threshold: float = Field(default=0.75, description="عتبة الثقة المعتمدة للمطابقة")
    similarity_score: float = Field(..., description="نسبة التطابق الدلالي واللفظي (بين 0.0 و 1.0)")
    is_authentic: bool = Field(default=True, description="هل الرواية معتمدة ومقبولة وفق معايير التوثيق")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "matched_text": "إنَّما الأَعْمالُ بالنِّيّاتِ، وإنَّما لِكُلِّ امْرِئٍ ما نَوَى...",
                "source": "صحيح البخاري",
                "hadith_number": "1",
                "chapter": "بدء الوحي",
                "grade": "صحيح",
                "narrator": "عمر بن الخطاب رضي الله عنه",
                "confidence_threshold": 0.75,
                "similarity_score": 0.98,
                "is_authentic": True
            }
        }
    }
