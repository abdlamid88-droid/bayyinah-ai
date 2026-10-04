from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.db.session import get_session
from app.models.hadith import HadithRecord
from app.schemas.verification import VerificationRequest, VerificationResponse
from app.schemas.evidence import EvidenceCardResponse

router = APIRouter()


@router.post("", response_model=VerificationResponse, summary="التحقق المعرفي من النصوص والروايات")
def verify_text(
    request: VerificationRequest,
    session: Session = Depends(get_session)
):
    """
    نقطة التحقق المعرفي المبدئية:
    - البحث عن المتون والروايات المتطابقة مع النص المدخل في المصادر المعتمدة.
    - استرجاع بطاقات الأدلة الموثقة (Evidence Cards).
    - تقديم تقييم أولي لدرجة الثبوت ومستوى التطابق.
    """
    cleaned_query = request.text.strip()

    # محاولة البحث عن نصوص مطابقة جزئياً أو كلياً في قاعدة البيانات
    statement = select(HadithRecord).where(
        HadithRecord.text_clean.contains(cleaned_query) |
        HadithRecord.text_raw.contains(cleaned_query)
    ).limit(request.limit)

    results = session.exec(statement).all()

    evidences = []
    for record in results:
        evidences.append(
            EvidenceCardResponse(
                id=record.id,
                matched_text=record.text_raw,
                source=record.source,
                hadith_number=record.hadith_number,
                chapter=record.chapter,
                grade=record.grade,
                narrator=record.narrator,
                confidence_threshold=request.confidence_threshold,
                similarity_score=0.95,  # نسبة تطابق أولية عند المطابقة المباشرة
                is_authentic=(record.grade in ["صحيح", "حسن", "متواتر"] if record.grade else True)
            )
        )

    # في حال كانت قاعدة البيانات فارغة أو لم يُعثر على تطابق مباشر، نقدم استجابة واضحة
    if evidences:
        verdict = "تم العثور على شواهد متطابقة وموثقة في المصادر المعتمدة"
    else:
        verdict = "لم يتم العثور على شواهد متطابقة مباشرة في القاعدة (يتطلب تفعيل التضمين الدلالي المتقدم)"

    return VerificationResponse(
        query=request.text,
        verdict=verdict,
        total_evidences=len(evidences),
        evidences=evidences
    )
