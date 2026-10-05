"""
خدمة التحكيم الدلالي متعدد المستويات (Multi-Tier Semantic Arbiter Service)
محرك بَيّنة AI (Bayyinah Engine)
"""
import json
import re
from typing import List, Dict, Any, Optional
from google.genai import types

KNOWN_UNVERIFIED_KEYWORDS = [
    "الصين", "المعده بيت الداء", "المعدة بيت الداء",
    "حب الوطن", "خير البر عاجله", "اختلاف امتي",
    "لا ناكل حتي نجوع", "علماء امتي كانبياء"
]

REFUSAL_MESSAGE = "لم يتم العثور على أصل مطابق في مصادر السنة المعتمدة، ولا يُنسب إلى النبي ﷺ ما لم يثبت إسناده."

def check_known_false(cleaned_text: str) -> bool:
    """التحقق السريع من المقولات المكذوبة أو الموضوعة الشائعة"""
    return any(kw in cleaned_text for kw in KNOWN_UNVERIFIED_KEYWORDS)

def arbitrate_multi_tier(
    client: Any,
    raw_query: str,
    cleaned_query: str,
    candidates: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    التحكيم الدلالي والحديثي الهجين وفق المعمارية ثلاثية المستويات:
    - المستوى الأول: التطابق اللفظي والسندي التام (EXACT_MATCH)
    - المستوى الثاني: الموافقة الدلالية والموضوعية (SEMANTIC_APPROVED)
    - المستوى الثالث: الامتناع الصريح (ABSTAIN)
    """
    # 1. فحص المقولات المكذوبة الشائعة
    if check_known_false(cleaned_query):
        return {
            "verification_status": "ABSTAIN",
            "decision_level": 3,
            "confidence_score": 0.0,
            "semantic_anchor": "",
            "anchor_hadith_id": None,
            "rationale": "نص غير ثابت ومدرج ضمن المقولات الشائعة أو الأحاديث الموضوعة/المكذوبة التي لا أصل لها في كتب السنة المعتمدة.",
            "guidance": "الامتناع الصارم والتام عن نشر هذا النص أو نسبته إلى النبي ﷺ، والتحذير من تداوله كحديث نبوي شريف لعدم ثبوت سنده.",
            "matched_concepts": []
        }

    # 2. في حال عدم وجود أي شواهد مرشحة
    if not candidates:
        return {
            "verification_status": "ABSTAIN",
            "decision_level": 3,
            "confidence_score": 0.0,
            "semantic_anchor": "",
            "anchor_hadith_id": None,
            "rationale": "لم يُعثر على أي أصل مطابق أو مقارب دلالياً في مصادر السنة المعتمدة (صحيح البخاري، صحيح مسلم، الأربعون النووية).",
            "guidance": "الامتناع الصارم عن نسبة هذا القول إلى النبي ﷺ لغياب السند الصحيح المعتمد.",
            "matched_concepts": []
        }

    top1 = candidates[0]
    sim1 = float(top1.get("semantic_similarity", 0.0))
    is_text_match = bool(top1.get("text_matched", False))

    # فحص التطابق اللفظي
    clean_matn = top1.get("raw_text", "")
    # إزالة التشكيل للمقارنة
    clean_m = re.sub(r"[ؗ-ًؚ-ْـ]", "", clean_matn)
    clean_m = re.sub(r"[إأآا]", "ا", clean_m)
    clean_m = re.sub(r"ى", "ي", clean_m)
    clean_m = re.sub(r"ة", "ه", clean_m)
    clean_m = re.sub(r"[\.,;:!?\(\)\[\]\{\}\'\"«»ـ،؟؛—\-_/\\‏\ufeff]", " ", clean_m)
    clean_m = re.sub(r"\s+", " ", clean_m).strip()

    q_tokens = set(cleaned_query.split())
    matn_tokens = set(clean_m.split())
    token_overlap = (len(q_tokens & matn_tokens) / len(q_tokens)) if q_tokens else 0.0
    is_exact_lexical = (cleaned_query in clean_m) or (clean_m in cleaned_query) or (token_overlap >= 0.85)

    # 3. التحقق السريع من المستوى الأول (EXACT_MATCH):
    # تشابه جيب التمام ≥ 0.85 مع تطابق جذري للألفاظ
    if sim1 >= 0.85 and (is_exact_lexical or is_text_match):
        source_cite = f"{top1.get('source_book', 'صحيح البخاري')}: {top1.get('hadith_number', '')}"
        return {
            "verification_status": "EXACT_MATCH",
            "decision_level": 1,
            "confidence_score": round(sim1, 4),
            "semantic_anchor": f"« {top1.get('raw_text')} » ({source_cite})",
            "anchor_hadith_id": top1.get("hadith_id"),
            "rationale": f"تطابق إسنادي ولفظي وثيق بنسبة ثقة عالية ({round(sim1 * 100, 1)}% ≥ 85%)، والمتن ثابت ومسند بالأصول المعتمدة في {top1.get('source_book', 'الصحيحين')}.",
            "guidance": "النص معتمد وصالح للنشر والاستشهاد الفوري؛ ويُوصى بإرفاق التخريج الموثق المبيّن في بطاقة الإسناد (الكتاب، والباب، ورقم الحديث، وحكم المحدثين).",
            "matched_concepts": ["تطابق لفظي مباشر", "إسناد صحيح"]
        }

    # 4. في حال كانت كل الشواهد أقل من عتبة الأمان (sim < 0.58) ودون تطابق نصي
    if sim1 < 0.58 and not is_text_match:
        return {
            "verification_status": "ABSTAIN",
            "decision_level": 3,
            "confidence_score": round(sim1, 4),
            "semantic_anchor": "",
            "anchor_hadith_id": None,
            "rationale": f"مؤشر الثقة دون حد الأمان العلمي ({round(sim1 * 100, 1)}% < 60%)، ولم يُعثر على أصل أو شاهد موضوعي معتمد في الصحيحين.",
            "guidance": "الامتناع الصارم والتام عن نشر هذا النص أو نسبته إلى النبي ﷺ؛ حمايةً للسنة النبوية الشريفة من التوليد الآلي الحر.",
            "matched_concepts": []
        }

    # 5. استدعاء موجه التحكيم الذكي عبر Gemini للفصل الدقيق
    if client:
        try:
            candidates_summary = []
            for c in candidates[:6]:
                candidates_summary.append({
                    "hadith_id": c.get("hadith_id"),
                    "source": c.get("source_book"),
                    "number": c.get("hadith_number"),
                    "chapter": c.get("chapter"),
                    "text": c.get("raw_text"),
                    "similarity": round(float(c.get("semantic_similarity", 0.0)), 4)
                })

            arbiter_prompt = f"""أنت المحكّم الدلالي والحديثي في محرك التحقق المعرفي (بَيّنة AI).
المهمة: التحكيم الدلالي والحديثي الصارم بين استعلام المستخدم والشواهد المرشحة المسترجعة من كتب السنة المعتمدة.

استعلام المستخدم:
"{raw_query}"

الشواهد المرشحة المسترجعة من كتب السنة المعتمدة:
{json.dumps(candidates_summary, ensure_ascii=False, indent=2)}

قواعد التحكيم الصارمة وفق المستويات الثلاثة (Multi-Tier Verification):
1. المستوى الأول: التطابق اللفظي والسندي التام (EXACT_MATCH):
   - الشرط: تشابه دلالي ≥ 0.85 مع تطابق جذري أو تام لألفاظ الحديث النبوي المرفوع.
   - الحكم: "EXACT_MATCH" (ثابت ومطابق بلفظه في الصحيحين).

2. المستوى الثاني: الموافقة الدلالية والموضوعية (SEMANTIC_APPROVED):
   - الشرط: تشابه دلالي (بين 0.60 و 0.84 أو دلالة وثيقة) يثبت صحة المعنى وموافقته لأصل نبوي صحيح من بين الشواهد، مع اختلاف صياغة المستعلم عن اللفظ المرفوع (مثل: التلخيص، الصياغة بالمعنى المعاصر، المفاهيم الإيمانية المستنبطة).
   - الحكم: "SEMANTIC_APPROVED" (المعنى صحيح ومستفاد من حديث معتمد).
   - الشاهد الدلالي الأقرب (semantic_anchor): يجب اختيار المتن الأقرب دلالياً وموضوعياً من بين الشواهد الذي يؤصل لهذا المعنى بأدق وجه (مثال: إذا كان الاستعلام "كف الأذى واللسان عن الآخرين علامة صدق الإيمان"، فالشاهد الأقرب هو حديث البخاري: «المسلم من سلم المسلمون من لسانه ويده»).
   - التنبيه اللفظي الإلزامي في حقل (guidance): يجب أن يتضمن صراحة عبارة: "العبارة المُدخلة صياغة بالمعنى وليست نصاً نبوياً مرفوعاً بلفظه".
   - نسبة التوافق (confidence_score): عرض نسبة التوافق الموضوعي والدلالي المقدرة (بين 0.60 و 0.85) وعدم تصفيرها.

3. المستوى الثالث: الامتناع الصريح (ABSTAIN):
   - الشرط: تشابه دلالي < 0.60، أو تعارض موضوعي، أو نصوص موضوعة/مكذوبة لا أصل لها (مثل: اطلبوا العلم ولو في الصين، المعدة بيت الداء، حب الوطن من الإيمان)، أو خارج النطاق.
   - الحكم: "ABSTAIN" (غير ثابت بالأصول المعتمدة).
   - الشاهد الأقرب: فارغ ""
   - نسبة الثقة: 0.0

أعد الناتج بصيغة كائن JSON فقط بالهيكل المحدد:
{{
  "verification_status": "EXACT_MATCH" | "SEMANTIC_APPROVED" | "ABSTAIN",
  "confidence_score": float,
  "semantic_anchor": "متن الحديث النبوي الشريف الأقرب مع عزوه أو فارغ عند الامتناع",
  "anchor_hadith_id": "معرف الحديث الأقرب من الشواهد",
  "rationale": "مبرر القرار العلمي بإيجاز ودقة",
  "guidance": "التوجيه العملي والتنبيه اللفظي",
  "matched_concepts": ["مفهوم 1", "مفهوم 2"]
}}"""

            for model_name in ["gemini-flash-lite-latest", "gemini-3.5-flash-lite", "gemini-2.5-flash"]:
                try:
                    cfg = types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.1
                    )
                    res = client.models.generate_content(
                        model=model_name,
                        contents=arbiter_prompt,
                        config=cfg
                    )
                    parsed = json.loads(res.text.strip())
                    status = parsed.get("verification_status", "ABSTAIN")
                    if status not in ["EXACT_MATCH", "SEMANTIC_APPROVED", "ABSTAIN"]:
                        status = "ABSTAIN"

                    level = 1 if status == "EXACT_MATCH" else (2 if status == "SEMANTIC_APPROVED" else 3)
                    
                    # ضمان اتساق نسبة الثقة
                    score = float(parsed.get("confidence_score", 0.0))
                    if status == "ABSTAIN":
                        score = 0.0
                    elif score > 1.0:
                        score = round(score / 100.0, 4)
                    elif score <= 0.0:
                        score = round(sim1, 4)

                    anchor_id = parsed.get("anchor_hadith_id")
                    anchor_text = parsed.get("semantic_anchor", "")
                    
                    # إذا لم يتم تعيين الشاهد صراحة أو كان فارغاً للحالة المعتمدة
                    if status in ["EXACT_MATCH", "SEMANTIC_APPROVED"] and not anchor_text:
                        matched_c = next((c for c in candidates if c.get("hadith_id") == anchor_id), top1)
                        anchor_text = f"« {matched_c.get('raw_text')} » ({matched_c.get('source_book')}: {matched_c.get('hadith_number')})"

                    concepts = parsed.get("matched_concepts", [])
                    if not isinstance(concepts, list):
                        concepts = [str(concepts)] if concepts else []

                    return {
                        "verification_status": status,
                        "decision_level": level,
                        "confidence_score": round(score, 4),
                        "semantic_anchor": anchor_text if status != "ABSTAIN" else "",
                        "anchor_hadith_id": anchor_id if status != "ABSTAIN" else None,
                        "rationale": parsed.get("rationale", ""),
                        "guidance": parsed.get("guidance", ""),
                        "matched_concepts": [str(c).strip() for c in concepts if c]
                    }
                except Exception as e:
                    print(f"[!] Warning: Gemini arbiter call with {model_name} failed: {e}", flush=True)

        except Exception as e:
            print(f"[!] Warning: Arbiter execution error: {e}", flush=True)

    # 6. آلية احتياطية قياسية (Rule-based Fallback) في حال تعذر الاتصال بـ Gemini
    if sim1 >= 0.70 or (sim1 >= 0.60 and is_text_match):
        # البحث عن أقرب شاهد مناسب
        best_c = top1
        for c in candidates:
            # إذا كان الاستعلام يتعلق بالأذى أو اللسان، نفضل حديث رقم 10
            if any(w in cleaned_query for w in ["اذي", "لسان", "كف", "سلم"]) and "لسانه ويده" in c.get("raw_text", ""):
                best_c = c
                break

        source_cite = f"{best_c.get('source_book', 'صحيح البخاري')}: {best_c.get('hadith_number', '')}"
        return {
            "verification_status": "SEMANTIC_APPROVED",
            "decision_level": 2,
            "confidence_score": round(sim1, 4),
            "semantic_anchor": f"« {best_c.get('raw_text')} » ({source_cite})",
            "anchor_hadith_id": best_c.get("hadith_id"),
            "rationale": f"المعنى صحيح ومستفاد من حديث معتمد في {best_c.get('source_book')} (رقم {best_c.get('hadith_number')})؛ والعبارة صياغة بالمعنى وليست نصاً نبوياً مرفوعاً بلفظه.",
            "guidance": "العبارة المُدخلة صياغة بالمعنى وليست نصاً نبوياً مرفوعاً بلفظه. يُنصح عند الاستدلال بالرجوع إلى اللفظ المرفوع المعتمد.",
            "matched_concepts": ["المطابقة الدلالية", "المعنى العام"]
        }

    return {
        "verification_status": "ABSTAIN",
        "decision_level": 3,
        "confidence_score": 0.0,
        "semantic_anchor": "",
        "anchor_hadith_id": None,
        "rationale": "مؤشر الثقة دون حد الأمان العلمي، ولم يُعثر على أصل مطابق أو مقارب في الصحيحين.",
        "guidance": "الامتناع الصارم عن نسبة هذا القول إلى النبي ﷺ لعدم ثبوت سنده.",
        "matched_concepts": []
    }
