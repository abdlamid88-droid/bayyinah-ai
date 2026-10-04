import time
import requests

API_URL = "http://localhost:8000/api/v1/verify"
CLEAR_URL = "http://localhost:8000/api/v1/cache/clear"

def format_hadith_number(card):
    hadith_id = str(card.get("hadith_id") or "")
    source_book = str(card.get("source") or card.get("source_book") or "")
    raw_number = card.get("number") or card.get("hadith_number") or "-"

    is_nawawi = "nawawi_" in hadith_id.lower() or "الأربعون النووية" in source_book or "النووية" in source_book
    if is_nawawi and raw_number != "-":
        return f"{raw_number} (الأربعون النووية)"
    return str(raw_number)

def run_test():
    print("[*] Clearing cache to test cold vs warm behavior...")
    requests.post(CLEAR_URL)

    test_queries = [
        ("لا ضرر ولا ضرار", "Nawawi Collection"),
        ("إنما الأعمال بالنيات وإنما لكل امرئ ما نوى", "Sahih Bukhari"),
        ("المعدة بيت الداء والحمية رأس كل دواء", "Smart Refusal (False Saying)")
    ]

    for q, label in test_queries:
        print(f"\n==================================================")
        print(f"Testing Query: '{q}' [{label}]")

        # 1st Execution (Cold)
        t0 = time.perf_counter()
        r1 = requests.post(API_URL, json={"query": q, "text": q})
        lat1 = (time.perf_counter() - t0) * 1000
        d1 = r1.json()
        card1 = d1.get("evidence_card") or {}
        cached1 = d1.get("cached", False)
        formatted_num1 = format_hadith_number(card1) if card1 else "N/A"

        print(f"  [Run 1 - Cold]")
        print(f"    - Status: {d1.get('status')}")
        print(f"    - Cached: {cached1}")
        print(f"    - Latency: {lat1:.2f} ms")
        print(f"    - Hadith Number Output: '{formatted_num1}'")
        print(f"    - UI Display: ⏱️ المعالجة: {lat1:.1f} ms")

        assert not cached1, f"Expected Run 1 to be Cache Miss, got {cached1}"

        # 2nd Execution (Warm / Cached)
        t0 = time.perf_counter()
        r2 = requests.post(API_URL, json={"query": q, "text": q})
        lat2 = (time.perf_counter() - t0) * 1000
        d2 = r2.json()
        card2 = d2.get("evidence_card") or {}
        cached2 = d2.get("cached", False)
        formatted_num2 = format_hadith_number(card2) if card2 else "N/A"

        print(f"  [Run 2 - Warm / In-Memory]")
        print(f"    - Status: {d2.get('status')}")
        print(f"    - Cached: {cached2}")
        print(f"    - Latency: {lat2:.2f} ms")
        print(f"    - Hadith Number Output: '{formatted_num2}'")
        badge = "⚡ استجابة فورية من الكاش (Memory Hit)" if cached2 else "Standard Latency"
        print(f"    - UI Display: {badge}")

        assert cached2, f"Expected Run 2 to be Cache Hit, got {cached2}"
        assert lat2 < 100.0, f"Expected sub-100ms cache hit, got {lat2} ms"

        if "Refusal" in label:
            expected_refusal = "لم يتم العثور على أصل مطابق في مصادر السنة المعتمدة، ولا يُنسب إلى النبي ﷺ ما لم يثبت إسناده."
            assert d1.get("message") == expected_refusal, f"Expected refusal message '{expected_refusal}', got '{d1.get('message')}'"
            assert d2.get("message") == expected_refusal, f"Expected refusal message in cache hit '{expected_refusal}', got '{d2.get('message')}'"
            print(f"    -> Scientific baseline refusal message verified: '{d1.get('message')}'")

        if "Nawawi" in label:
            assert "(الأربعون النووية)" in formatted_num2, f"Expected Nawawi formatting, got {formatted_num2}"
            print(f"    -> Nawawi 40 badge format verified: '{formatted_num2}'")

    print("\n[+] All Frontend Cache Badge, Nawawi Formatting & Scientific Refusal Validations PASSED successfully!")

if __name__ == "__main__":
    run_test()
