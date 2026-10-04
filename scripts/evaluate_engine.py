import os
import time
from datetime import datetime
import requests
from tabulate import tabulate

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api/v1/verify")
REPORT_PATH = os.getenv("REPORT_PATH", "/app/reports/benchmark_v0.3.2.md")

# 15 حالة اختبار شاملة تغطي كافة المتون والسيناريوهات
TEST_CASES = [
    # --- مطابقة لفظية دقيقة ---
    {
        "query": "إنما الأعمال بالنيات وإنما لكل امرئ ما نوى",
        "expected_status": "verified",
        "category": "Exact Lexical (صحيح البخاري: 1)"
    },
    {
        "query": "بني الإسلام على خمس شهادة أن لا إله إلا الله",
        "expected_status": "verified",
        "category": "Exact Lexical (صحيح مسلم: 8)"
    },
    {
        "query": "المسلم من سلم المسلمون من لسانه ويده",
        "expected_status": "verified",
        "category": "Exact Lexical (صحيح البخاري: 10)"
    },
    # --- مطابقة دلالية معاصرة (أحاديث مستوردة) ---
    {
        "query": "السعي في تحصيل العلم ييسر الدخول إلى الجنة",
        "expected_status": "verified",
        "category": "Semantic Match (صحيح مسلم: 2699)"
    },
    {
        "query": "الأثر الباقي للإنسان بعد وفاته من الصدقات والأولاد",
        "expected_status": "verified",
        "category": "Semantic Match (صحيح مسلم: 1631)"
    },
    {
        "query": "معاملة الناس باليسر ونبذ التنفير والتشديد",
        "expected_status": "verified",
        "category": "Semantic Match (صحيح البخاري: 67)"
    },
    {
        "query": "كف الأذى واللسان عن الناس علامة صدق الإيمان وسلامة القلب",
        "expected_status": "verified",
        "category": "Semantic Match (صحيح البخاري: 10)"
    },
    {
        "query": "إرادة الخير والتوجيه الصادق للمجتمع وعامة الناس",
        "expected_status": "verified",
        "category": "Semantic Match (صحيح مسلم: 55)"
    },
    {
        "query": "عواقب أكل أموال الناس بالباطل والاعتداء عليهم يوم الحساب",
        "expected_status": "verified",
        "category": "Semantic Match (صحيح مسلم: 2564)"
    },
    {
        "query": "أن يتمنى المسلم لأخيه الخير والصلاح كما يرجوه لنفسه",
        "expected_status": "verified",
        "category": "Semantic Match (صحيح البخاري: 13)"
    },
    # --- نصوص مفبركة وأقوال دارجة (Smart Refusal) ---
    {
        "query": "المعدة بيت الداء والحمية رأس الدواء",
        "expected_status": "refused",
        "category": "False/Proverb (قول دارج)"
    },
    {
        "query": "اطلبوا العلم ولو في الصين",
        "expected_status": "refused",
        "category": "Unverified/Weak (حديث لا يثبت)"
    },
    {
        "query": "حب الوطن من الإيمان",
        "expected_status": "refused",
        "category": "Unverified (موضوع/شائع)"
    },
    {
        "query": "خير البر عاجله",
        "expected_status": "refused",
        "category": "False/Proverb (مثل سائر)"
    },
    {
        "query": "الذكاء الاصطناعي وهندسة البيانات في الحوسبة السحابية",
        "expected_status": "refused",
        "category": "Out of Domain (نص تقني معاصر)"
    }
]

def generate_markdown_report(table_str, total_tests, accuracy, recall, specificity, avg_lat, min_lat, max_lat):
    report_content = f"""# تقرير التقييم المعياري لمحرك بيّنة AI
**الإصدار:** `v0.3.2`  
**تاريخ التقييم:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`  
**نطاق الاختبار:** فحص البحث الهجين (FTS + Vector) وآلية الرفض الذكي (Smart Refusal)

---

## 📊 المؤشرات الإحصائية العامة

| المؤشر | القيمة المحققة | المستهدف الهندسي | الحالة |
| :--- | :---: | :---: | :---: |
| **الدقة الكلية (Overall Accuracy)** | **{accuracy:.2f}%** | 95.00%+ | {'✅ متطابق' if accuracy >= 95 else '⚠️ يحتاج مراجعة'} |
| **حساسية التحقق (Recall)** | **{recall:.2f}%** | 95.00%+ | {'✅ متطابق' if recall >= 95 else '⚠️ يحتاج مراجعة'} |
| **دقة الرفض الذكي (Rejection Specificity)** | **{specificity:.2f}%** | 95.00%+ | {'✅ متطابق' if specificity >= 95 else '⚠️ يحتاج مراجعة'} |
| **متوسط زمن الاستجابة (Latency)** | **{avg_lat:.2f} ms** | < 600 ms | {'✅ متطابق' if avg_lat < 600 else '⚠️ أعلى من المستهدف'} |
| **نطاق الأزمنة (Min / Max)** | **{min_lat:.2f} ms / {max_lat:.2f} ms** | - | - |

---

## 📋 تفاصيل نتائج حالات الاختبار ({total_tests} حالة)

{table_str}

---

## 🛠️ تفاصيل المعمارية وضوابط التحقق:
- **البحث الهجين:** دمج نتائج البحث اللفظي (GIN/tsvector) مع البحث الشعاعي (HNSW/vector_cosine_ops) باستخدام Reciprocal Rank Fusion (RRF).
- **عتبة الرفض الذكي:** اشتراط تجاوز نسبة التطابق الدلالي الصرف حاجز **0.78** في حال انعدام التطابق اللفظي، لمنع الهلوسة في المتون المشابهة موضوعياً.
"""
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"\n[+] تم حفظ تقرير التقييم بنجاح في: {REPORT_PATH}")

def run_benchmark():
    print(f"[*] بدء تشغيل التقييم المعياري الشامل عبر: {API_URL}\n")
    results_table = []
    latencies = []
    correct_verifications = 0
    correct_refusals = 0
    total_positives = sum(1 for tc in TEST_CASES if tc["expected_status"] == "verified")
    total_negatives = sum(1 for tc in TEST_CASES if tc["expected_status"] == "refused")

    for idx, tc in enumerate(TEST_CASES, 1):
        query = tc["query"]
        expected = tc["expected_status"]
        category = tc["category"]

        start_t = time.perf_counter()
        try:
            res = requests.post(API_URL, json={"query": query}, timeout=10)
            duration_ms = (time.perf_counter() - start_t) * 1000
            latencies.append(duration_ms)

            if res.status_code == 200:
                data = res.json()
                actual = data.get("status")
                card = data.get("evidence_card") or {}
                similarity = card.get("semantic_similarity", 0.0)

                passed = (actual == expected)
                if passed:
                    if expected == "verified":
                        correct_verifications += 1
                    else:
                        correct_refusals += 1

                status_mark = "✅ PASS" if passed else "❌ FAIL"
                results_table.append([
                    idx,
                    query[:30] + ("..." if len(query) > 30 else ""),
                    category,
                    expected,
                    actual,
                    f"{similarity * 100:.1f}%" if similarity else "-",
                    f"{duration_ms:.1f}ms",
                    status_mark
                ])
            else:
                results_table.append([idx, query[:30], category, expected, f"HTTP {res.status_code}", "-", f"{duration_ms:.1f}ms", "❌ FAIL"])
        except Exception as e:
            duration_ms = (time.perf_counter() - start_t) * 1000
            latencies.append(duration_ms)
            results_table.append([idx, query[:30], category, expected, f"ERR: {type(e).__name__}", "-", f"{duration_ms:.1f}ms", "❌ FAIL"])

    headers = ["#", "الاستعلام", "التصنيف", "المتوقع", "الفعلي", "التشابه", "الزمن", "النتيجة"]
    table_str = tabulate(results_table, headers=headers, tablefmt="github")
    print(table_str)

    total_tests = len(TEST_CASES)
    accuracy = ((correct_verifications + correct_refusals) / total_tests) * 100
    verification_recall = (correct_verifications / total_positives) * 100 if total_positives else 0
    rejection_specificity = (correct_refusals / total_negatives) * 100 if total_negatives else 0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    min_latency = min(latencies) if latencies else 0
    max_latency = max(latencies) if latencies else 0

    print("\n" + "=" * 55)
    print("📊 ملخص المؤشرات الإحصائية (Metrics Summary):")
    print("=" * 55)
    print(f"• إجمالي الاختبارات:        {total_tests}")
    print(f"• الدقة الكلية (Accuracy):      {accuracy:.2f}%")
    print(f"• حساسية التحقق (Recall):       {verification_recall:.2f}% ({correct_verifications}/{total_positives})")
    print(f"• دقة الرفض الذكي (Rejection): {rejection_specificity:.2f}% ({correct_refusals}/{total_negatives})")
    print(f"• متوسط زمن الاستجابة:       {avg_latency:.2f} ms")
    print(f"• أقل زمن / أقصى زمن:       {min_latency:.2f} ms / {max_latency:.2f} ms")
    print("=" * 55)

    generate_markdown_report(
        table_str, total_tests, accuracy, verification_recall, rejection_specificity,
        avg_latency, min_latency, max_latency
    )

if __name__ == "__main__":
    run_benchmark()
