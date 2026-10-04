import os
import json
import time
import requests

API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1/verify")
CACHE_CLEAR_URL = os.getenv("CACHE_CLEAR_URL", "http://localhost:8000/api/v1/cache/clear")

def run_explainability_tests():
    print("=" * 60)
    print("🚀 بدء اختبارات طبقة التفسير الدلالي (Semantic Explainability)")
    print("=" * 60)

    # 0. تفريغ الكاش
    requests.post(CACHE_CLEAR_URL, timeout=5)
    time.sleep(0.5)

    # 1. اختبار التطابق اللفظي المباشر (Exact Lexical Match)
    q_exact = "إنما الأعمال بالنيات وإنما لكل امرئ ما نوى"
    print(f"\n[*] 1. اختبار التطابق اللفظي المباشر:\n    الاستعلام: '{q_exact}'")
    t0 = time.perf_counter()
    r1 = requests.post(API_URL, json={"text": q_exact}, timeout=20)
    lat1 = (time.perf_counter() - t0) * 1000
    assert r1.status_code == 200, f"HTTP Error: {r1.status_code}"
    d1 = r1.json()

    print(f"    - الحالة: {d1.get('status')}")
    print(f"    - درجة التشابه: {d1.get('similarity_score')}")
    print(f"    - زمن الاستجابة: {d1.get('latency_ms')} ms")
    print(f"    - نوع التحليل الدلالي: {type(d1.get('alignment_insight')).__name__}")
    print(f"    - القيمة: {d1.get('alignment_insight')}")

    assert d1.get("status") == "verified"
    assert d1.get("alignment_insight") == "تطابق لفظي مباشر مع متن الحديث المعتمد في الباب.", \
        f"Unexpected alignment_insight: {d1.get('alignment_insight')}"
    print("    ✅ نجح اختبار التطابق اللفظي المباشر.")

    # 2. اختبار الصياغة الدلالية المعاصرة (Semantic Paraphrase)
    q_semantic = "كف الأذى واللسان عن الآخرين علامة صدق الإيمان"
    print(f"\n[*] 2. اختبار الصياغة الدلالية المعاصرة:\n    الاستعلام: '{q_semantic}'")
    t0 = time.perf_counter()
    r2 = requests.post(API_URL, json={"text": q_semantic}, timeout=30)
    lat2 = (time.perf_counter() - t0) * 1000
    assert r2.status_code == 200, f"HTTP Error: {r2.status_code}"
    d2 = r2.json()

    print(f"    - الحالة: {d2.get('status')}")
    print(f"    - درجة التشابه: {d2.get('similarity_score')}")
    print(f"    - زمن الاستجابة: {d2.get('latency_ms')} ms")
    insight2 = d2.get("alignment_insight")
    print(f"    - المفاهيم المستخرجة: {insight2.get('matched_concepts') if isinstance(insight2, dict) else None}")
    print(f"    - الشرح العلمي المؤصل: {insight2.get('explanation') if isinstance(insight2, dict) else None}")

    assert d2.get("status") == "verified"
    assert isinstance(insight2, dict), "alignment_insight must be a dictionary for semantic queries"
    assert "matched_concepts" in insight2 and len(insight2["matched_concepts"]) > 0, "Missing matched_concepts"
    assert "explanation" in insight2 and len(insight2["explanation"]) > 10, "Missing valid explanation"
    print("    ✅ نجح اختبار توليد التحليل والمفاهيم الدلالية المشتركة.")

    # 3. اختبار استرجاع التحليل من الذاكرة المؤقتة (Cache Hit)
    print(f"\n[*] 3. اختبار استرجاع النتيجة والتحليل من الكاش (Memory Hit):")
    t0 = time.perf_counter()
    r3 = requests.post(API_URL, json={"text": q_semantic}, timeout=5)
    lat3 = (time.perf_counter() - t0) * 1000
    assert r3.status_code == 200
    d3 = r3.json()

    print(f"    - من الكاش: {d3.get('cached')}")
    print(f"    - زمن الاستجابة الفعلي: {lat3:.2f} ms (المسجل داخلياً: {d3.get('latency_ms')} ms)")
    assert d3.get("cached") is True, "Expected cached == True"
    assert d3.get("alignment_insight") == d2.get("alignment_insight"), "Cached alignment_insight mismatch"
    print("    ✅ نجح اختبار الكاش واسترجاع التحليل فورياً (< 5ms).")

    # 4. اختبار الرفض الذكي (Smart Refusal)
    q_refused = "اطلبوا العلم ولو في الصين"
    print(f"\n[*] 4. اختبار نفي النسبة والرفض الذكي:\n    الاستعلام: '{q_refused}'")
    r4 = requests.post(API_URL, json={"text": q_refused}, timeout=10)
    assert r4.status_code == 200
    d4 = r4.json()

    print(f"    - الحالة: {d4.get('status')}")
    print(f"    - الرسالة المعتمدة: {d4.get('message')}")
    print(f"    - alignment_insight: {d4.get('alignment_insight')}")

    assert d4.get("status") == "refused"
    assert d4.get("alignment_insight") is None
    print("    ✅ نجح اختبار الرفض الذكي مع خلو التحليل الدلالي.")

    print("\n" + "=" * 60)
    print("🎉 جميع اختبارات طبقة التفسير الدلالي (Semantic Explainability) اجتازت بنجاح 100%!")
    print("=" * 60)

if __name__ == "__main__":
    run_explainability_tests()
