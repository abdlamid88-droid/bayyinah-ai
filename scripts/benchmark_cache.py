import os
import sys
import time
import json
import requests

API_BASE = os.getenv("BENCHMARK_API_BASE", "http://localhost:8000")
VERIFY_URL = f"{API_BASE}/api/v1/verify"
STATS_URL = f"{API_BASE}/api/v1/cache/stats"
CLEAR_URL = f"{API_BASE}/api/v1/cache/clear"

TEST_QUERIES = [
    # Direct Matches
    {"id": 1, "category": "Direct Match", "base": "إنما الأعمال بالنيات وإنما لكل امرئ ما نوى", "expected": "verified"},
    {"id": 2, "category": "Direct Match", "base": "المسلم من سلم المسلمون من لسانه ويده", "expected": "verified"},
    {"id": 3, "category": "Direct Match", "base": "من سلك طريقا يلتمس فيه علما سهل الله له به طريقا إلى الجنة", "expected": "verified"},
    {"id": 4, "category": "Direct Match", "base": "بني الإسلام على خمس شهادة أن لا إله إلا الله", "expected": "verified"},
    {"id": 5, "category": "Direct Match", "base": "لا يؤمن أحدكم حتى يحب لأخيه ما يحب لنفسه", "expected": "verified"},
    # Semantic Paraphrases
    {"id": 6, "category": "Semantic Paraphrase", "base": "صلاح الأعمال ومراتب قبولها مرتبط بنوايا أصحابها", "expected": "verified"},
    {"id": 7, "category": "Semantic Paraphrase", "base": "كف الأذى واللسان عن الآخرين علامة صدق الإيمان", "expected": "verified"},
    {"id": 8, "category": "Semantic Paraphrase", "base": "السعي والاجتهاد في تحصيل العلم ييسر الدخول إلى الجنة", "expected": "verified"},
    # Smart Refusal
    {"id": 9, "category": "Smart Refusal", "base": "المعدة بيت الداء والحمية رأس كل دواء", "expected": "refused"},
    {"id": 10, "category": "Smart Refusal", "base": "اطلبوا العلم ولو في الصين", "expected": "refused"},
    {"id": 11, "category": "Smart Refusal", "base": "حب الوطن من الإيمان", "expected": "refused"},
]

# Normalization variants to test invariance in caching
NORMALIZATION_VARIANTS = [
    {
        "id": 1,
        "desc": "Tashkeel + Tatweel addition",
        "original": "إنما الأعمال بالنيات وإنما لكل امرئ ما نوى",
        "variant": "إِنَّـــمَا الأَعْـــمَالُ بِالنِّيَّـــاتِ وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى."
    },
    {
        "id": 2,
        "desc": "Alef normalization (Bare Alef) + stripped spacing",
        "original": "المسلم من سلم المسلمون من لسانه ويده",
        "variant": "المسلم   من سلم المسلمون من لسانه ويده  "
    },
    {
        "id": 3,
        "desc": "Tanween and diacritics injection",
        "original": "من سلك طريقا يلتمس فيه علما سهل الله له به طريقا إلى الجنة",
        "variant": "مَنْ سَلَكَ طَرِيقاً يَلْتَمِسُ فِيهِ عِلْماً سَهَّلَ اللهُ لَهُ بِهِ طَرِيقاً إِلَى الجَنَّةِ"
    },
    {
        "id": 4,
        "desc": "Alef variants & punctuation",
        "original": "بني الإسلام على خمس شهادة أن لا إله إلا الله",
        "variant": "«بني الاسلام علي خمس: شهاده ان لا اله الا الله»"
    },
    {
        "id": 5,
        "desc": "Taa Marbuta / Haa variation",
        "original": "المعدة بيت الداء والحمية رأس كل دواء",
        "variant": "المعده بيت الداء والحميه راس كل دواء"
    },
    {
        "id": 6,
        "desc": "Tatweel + quotes",
        "original": "حب الوطن من الإيمان",
        "variant": "«حـــب الـــوطـــن مـــن الإيـــمـــان»"
    }
]

def clear_cache():
    try:
        res = requests.post(CLEAR_URL, timeout=10)
        return res.status_code == 200
    except Exception as e:
        print(f"[!] Warning: could not clear cache: {e}")
        return False

def get_cache_stats():
    try:
        res = requests.get(STATS_URL, timeout=10)
        return res.json().get("cache", {})
    except Exception as e:
        print(f"[!] Warning: could not fetch cache stats: {e}")
        return {}

def run_query(text: str):
    t0 = time.perf_counter()
    res = requests.post(VERIFY_URL, json={"query": text}, timeout=35)
    lat_ms = (time.perf_counter() - t0) * 1000.0
    data = res.json() if res.status_code == 200 else {}
    return {
        "status_code": res.status_code,
        "latency_ms": round(lat_ms, 2),
        "cached": data.get("cached", False),
        "status": data.get("status", "error"),
        "similarity": data.get("evidence_card", {}).get("semantic_similarity", 0.0) if data.get("evidence_card") else 0.0
    }

def profile_cache():
    print("[*] Starting Arabic-Aware In-Memory Cache Profiling...", flush=True)
    clear_cache()

    # Phase 1: Cold Cache (Cache Miss)
    print("\n--- Phase 1: Measuring Cold Cache (Cache Misses) ---", flush=True)
    miss_results = []
    for item in TEST_QUERIES:
        q = item["base"]
        res = run_query(q)
        is_correct = (res["status"].lower() == item["expected"].lower())
        miss_results.append({
            "id": item["id"],
            "query": q,
            "category": item["category"],
            "latency_ms": res["latency_ms"],
            "cached": res["cached"],
            "status": res["status"],
            "passed": is_correct
        })
        print(f"  [MISS] Q{item['id']} ({item['category']}): {res['latency_ms']} ms | Cached: {res['cached']} | Status: {res['status']}")

    # Phase 2: Warm Cache (Exact Cache Hit)
    print("\n--- Phase 2: Measuring Warm Cache (Exact Cache Hits) ---", flush=True)
    hit_exact_results = []
    for item in TEST_QUERIES:
        q = item["base"]
        res = run_query(q)
        hit_exact_results.append({
            "id": item["id"],
            "query": q,
            "latency_ms": res["latency_ms"],
            "cached": res["cached"],
            "status": res["status"]
        })
        print(f"  [HIT-EXACT] Q{item['id']}: {res['latency_ms']} ms | Cached: {res['cached']} | Status: {res['status']}")

    # Phase 3: Arabic Normalization Invariance (Variant Cache Hit)
    print("\n--- Phase 3: Measuring Arabic Normalization Invariance (Hit on Variations) ---", flush=True)
    variant_results = []
    for item in NORMALIZATION_VARIANTS:
        q = item["variant"]
        res = run_query(q)
        variant_results.append({
            "id": item["id"],
            "desc": item["desc"],
            "original": item["original"],
            "variant": q,
            "latency_ms": res["latency_ms"],
            "cached": res["cached"],
            "status": res["status"]
        })
        print(f"  [HIT-VARIANT] Q{item['id']} ({item['desc']}): {res['latency_ms']} ms | Cached: {res['cached']}")

    # Calculate Aggregated Metrics
    miss_latencies = [r["latency_ms"] for r in miss_results]
    hit_exact_latencies = [r["latency_ms"] for r in hit_exact_results]
    variant_latencies = [r["latency_ms"] for r in variant_results]
    all_hit_latencies = hit_exact_latencies + variant_latencies

    avg_miss = sum(miss_latencies) / len(miss_latencies)
    avg_hit = sum(all_hit_latencies) / len(all_hit_latencies)
    sorted_miss = sorted(miss_latencies)
    sorted_hit = sorted(all_hit_latencies)

    speedup = avg_miss / avg_hit if avg_hit > 0 else 0.0
    latency_drop_pct = ((avg_miss - avg_hit) / avg_miss) * 100.0

    stats = get_cache_stats()

    summary = {
        "cache_miss": {
            "count": len(miss_latencies),
            "avg_ms": round(avg_miss, 2),
            "min_ms": round(min(miss_latencies), 2),
            "max_ms": round(max(miss_latencies), 2),
            "p95_ms": round(sorted_miss[int(len(sorted_miss) * 0.95)], 2)
        },
        "cache_hit": {
            "count": len(all_hit_latencies),
            "avg_ms": round(avg_hit, 2),
            "min_ms": round(min(all_hit_latencies), 2),
            "max_ms": round(max(all_hit_latencies), 2),
            "p95_ms": round(sorted_hit[int(len(sorted_hit) * 0.95)], 2)
        },
        "performance_gain": {
            "speedup_factor": round(speedup, 2),
            "latency_reduction_percent": round(latency_drop_pct, 2),
            "sub_50ms_sla_met": all(lat < 50.0 for lat in all_hit_latencies)
        },
        "normalization_invariance": {
            "total_tested": len(variant_results),
            "all_hit_cache": all(r["cached"] for r in variant_results)
        },
        "cache_stats": stats
    }

    full_report = {
        "summary": summary,
        "phase1_miss_details": miss_results,
        "phase2_hit_exact_details": hit_exact_results,
        "phase3_normalization_details": variant_results
    }

    os.makedirs("reports", exist_ok=True)
    with open("reports/cache_benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(full_report, f, ensure_ascii=False, indent=2)

    print("\n" + "="*60)
    print("📊 CACHE PROFILING SUMMARY:")
    print(f"  - Cache Miss Avg Latency: {summary['cache_miss']['avg_ms']} ms")
    print(f"  - Cache Hit Avg Latency:  {summary['cache_hit']['avg_ms']} ms (Target < 50 ms)")
    print(f"  - Speedup Factor:         {summary['performance_gain']['speedup_factor']}x")
    print(f"  - Latency Reduction:      {summary['performance_gain']['latency_reduction_percent']}%")
    print(f"  - Normalization Invariance: {'✅ 100% Hits' if summary['normalization_invariance']['all_hit_cache'] else '❌ Failed'}")
    print(f"  - Sub-50ms SLA:           {'✅ PASSED' if summary['performance_gain']['sub_50ms_sla_met'] else '❌ FAILED'}")
    print("="*60)

    return full_report

if __name__ == "__main__":
    profile_cache()
