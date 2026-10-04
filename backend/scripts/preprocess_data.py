import re
import json

def clean_arabic_text(text: str) -> str:
    # إزالة التشكيل وعلامات الضبط
    tashkeel_pattern = re.compile(r'[\u0617-\u061A\u064B-\u0652]')
    text = re.sub(tashkeel_pattern, '', text)
    
    # إزالة التطويل (الكشيدة)
    text = re.sub(r'\u0640', '', text)
    
    # توحيد أشكال الألف والياء والتاء المربوطة لتسريع وتوحيد البحث
    text = re.sub(r'[إأآا]', 'ا', text)
    text = re.sub(r'ى', 'ي', text)
    text = re.sub(r'ة', 'ه', text)
    
    # تنظيف الفراغات الزائدة
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def process_hadith_entry(entry: dict) -> dict:
    if "clean_text" not in entry or not entry["clean_text"]:
        entry["clean_text"] = clean_arabic_text(entry.get("raw_text", ""))
    return entry

if __name__ == "__main__":
    sample = {
        "hadith_id": "bukhari_1",
        "raw_text": "إنَّما الأعْمالُ بالنِّيّاتِ، وإنَّما لِكُلِّ امْرِئٍ ما نَوى...",
        "source_book": "صحيح البخاري",
        "chapter": "بدء الوحي",
        "hadith_number": "1",
        "grade": "صحيح",
        "scholar_verdict": "أخرجه البخاري في صحيحه"
    }
    processed = process_hadith_entry(sample)
    print("النتيجة بعد التنظيف والتجهيز:")
    print(json.dumps(processed, ensure_ascii=False, indent=2))
