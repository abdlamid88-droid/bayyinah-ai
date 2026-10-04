import os
import time
import json
import requests

API_URL = os.getenv("BENCHMARK_API_URL", "http://localhost:8000/api/v1/verify")

TEST_CASES = [
    # Direct Matches (Authentic text verbatim)
    {"id": 1, "category": "Direct Match", "expected": "verified", "query": "إنما الأعمال بالنيات وإنما لكل امرئ ما نوى"},
    {"id": 2, "category": "Direct Match", "expected": "verified", "query": "المسلم من سلم المسلمون من لسانه ويده"},
    {"id": 3, "category": "Direct Match", "expected": "verified", "query": "من سلك طريقا يلتمس فيه علما سهل الله له به طريقا إلى الجنة"},
    {"id": 4, "category": "Direct Match", "expected": "verified", "query": "بني الإسلام على خمس شهادة أن لا إله إلا الله"},
    {"id": 5, "category": "Direct Match", "expected": "verified", "query": "لا يؤمن أحدكم حتى يحب لأخيه ما يحب لنفسه"},

    # Semantic Paraphrases (Modern phrasing / indirect meaning)
    {"id": 6, "category": "Semantic Paraphrase", "expected": "verified", "query": "صلاح الأعمال ومراتب قبولها مرتبط بنوايا أصحابها"},
    {"id": 7, "category": "Semantic Paraphrase", "expected": "verified", "query": "كف الأذى واللسان عن الآخرين علامة صدق الإيمان"},
    {"id": 8, "category": "Semantic Paraphrase", "expected": "verified", "query": "السعي والاجتهاد في تحصيل العلم ييسر الدخول إلى الجنة"},
    {"id": 9, "category": "Semantic Paraphrase", "expected": "verified", "query": "أركان وقواعد دين الإسلام خمسة أمور أساسية"},
    {"id": 10, "category": "Semantic Paraphrase", "expected": "verified", "query": "محبة الخير والنفع للناس من كمال إيمان المسلم"},

    # Smart Refusal / Negative Controls (Unauthentic, fabricated, or common sayings)
    {"id": 11, "category": "Smart Refusal", "expected": "refused", "query": "المعدة بيت الداء والحمية رأس كل دواء"},
    {"id": 12, "category": "Smart Refusal", "expected": "refused", "query": "اطلبوا العلم ولو في الصين"},
    {"id": 13, "category": "Smart Refusal", "expected": "refused", "query": "حب الوطن من الإيمان"},
    {"id": 14, "category": "Smart Refusal", "expected": "refused", "query": "اختلاف أمتي رحمة واسعة"},
    {"id": 15, "category": "Smart Refusal", "expected": "refused", "query": "نحن قوم لا نأكل حتى نجوع وإذا أكلنا لا نشبع"},
]

def evaluate():
    results = []
    latencies = []
    correct_count = 0

    for item in TEST_CASES:
        payload = {"text": item["query"], "query": item["query"]}
        t0 = time.perf_counter()
        try:
            res = requests.post(API_URL, json=payload, timeout=35)
            lat = (time.perf_counter() - t0) * 1000
            latencies.append(lat)

            if res.status_code == 200:
                data = res.json()
                status = data.get("status")
                if not status:
                    status = "verified" if data.get("evidence_card") else "refused"

                passed = (status.lower() == item["expected"].lower())
                if passed:
                    correct_count += 1

                card = data.get("evidence_card") or {}
                sim = card.get("semantic_similarity", 0.0)

                results.append({
                    **item,
                    "actual": status,
                    "passed": passed,
                    "similarity": round(float(sim), 4),
                    "latency_ms": round(lat, 2)
                })
            else:
                results.append({
                    **item,
                    "actual": f"HTTP_{res.status_code}",
                    "passed": False,
                    "similarity": 0.0,
                    "latency_ms": round(lat, 2)
                })
        except Exception as e:
            results.append({
                **item,
                "actual": f"ERROR: {str(e)[:30]}",
                "passed": False,
                "similarity": 0.0,
                "latency_ms": 0.0
            })

    # Summary metrics
    total = len(TEST_CASES)
    acc = (correct_count / total) * 100
    avg_lat = sum(latencies) / len(latencies) if latencies else 0.0
    sorted_lat = sorted(latencies)
    p95_lat = sorted_lat[int(len(sorted_lat) * 0.95)] if sorted_lat else 0.0

    report = {
        "summary": {
            "total_queries": total,
            "passed": correct_count,
            "failed": total - correct_count,
            "accuracy_percentage": round(acc, 2),
            "avg_latency_ms": round(avg_lat, 2),
            "p95_latency_ms": round(p95_lat, 2)
        },
        "details": results
    }

    os.makedirs("reports", exist_ok=True)
    with open("reports/benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return report

if __name__ == "__main__":
    rep = evaluate()
    print(f"[+] Benchmark completed: {rep['summary']['passed']}/{rep['summary']['total_queries']} passed ({rep['summary']['accuracy_percentage']}%)")
