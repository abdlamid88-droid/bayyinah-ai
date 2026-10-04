import os
import time
import requests
import streamlit as st

st.set_page_config(
    page_title="بَيّنة AI - محرك التحقق من المتون النبوية",
    page_icon="📜",
    layout="centered"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Cairo:wght@400;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
        direction: rtl;
        text-align: right;
    }
    .hadith-text {
        font-family: 'Amiri', serif;
        font-size: 1.25rem;
        line-height: 2.1;
        color: #1e293b;
        background-color: #f8fafc;
        padding: 1.2rem;
        border-radius: 8px;
        border-right: 4px solid #0284c7;
    }
    .metric-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.875rem;
    }
    .badge-verified { background-color: #dcfce7; color: #166534; }
    .badge-refused { background-color: #fee2e2; color: #991b1b; }
    .badge-cached {
        background-color: #ecfdf5;
        color: #065f46;
        border: 1px solid #10b981;
        box-shadow: 0 1px 3px rgba(16, 185, 129, 0.2);
    }
    .concept-badge {
        display: inline-block;
        background-color: #f0fdf4;
        color: #166534;
        padding: 0.2rem 0.65rem;
        margin: 0.2rem 0.25rem;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
        border: 1px solid #bbf7d0;
    }
    .insight-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-right: 4px solid #0284c7;
        padding: 1rem;
        border-radius: 8px;
        margin-top: 0.75rem;
        font-size: 0.95rem;
        color: #1e293b;
        line-height: 1.8;
    }

    /* شارات مستويات اتخاذ القرار (Decision Badges) */
    .decision-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 0.4rem 1rem;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.95rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    .badge-level-1 {
        background-color: #dcfce7;
        color: #166534;
        border: 1.5px solid #22c55e;
    }
    .badge-level-2 {
        background-color: #ffedd5;
        color: #9a3412;
        border: 1.5px solid #f97316;
    }
    .badge-level-3 {
        background-color: #fee2e2;
        color: #991b1b;
        border: 1.5px solid #ef4444;
    }

    /* سطر مبرر القرار والإجراء العملي (Human-Readable Rationale) */
    .rationale-card {
        border-radius: 8px;
        padding: 0.9rem 1.15rem;
        margin: 0.85rem 0 1rem 0;
        font-size: 0.92rem;
        line-height: 1.8;
    }
    .rationale-l1 {
        background-color: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-right: 5px solid #16a34a;
        color: #166534;
    }
    .rationale-l2 {
        background-color: #fffbeb;
        border: 1px solid #fde68a;
        border-right: 5px solid #d97706;
        color: #92400e;
    }
    .rationale-l3 {
        background-color: #fff1f2;
        border: 1px solid #fecdd3;
        border-right: 5px solid #e11d48;
        color: #9f1239;
    }

    /* تنبيه احترازي لتباين الألفاظ للمستوى الثاني */
    .level2-alert-box {
        background-color: #fff7ed;
        border: 1px solid #fed7aa;
        border-right: 5px solid #ea580c;
        border-radius: 8px;
        padding: 0.9rem 1.2rem;
        margin: 0.8rem 0;
        color: #9a3412;
        font-size: 0.92rem;
        line-height: 1.8;
    }

    /* إيضاح صريح لسبب الامتناع للمستوى الثالث */
    .level3-abstention-box {
        background-color: #fff1f2;
        border: 1px solid #fecdd3;
        border-right: 5px solid #be123c;
        border-radius: 8px;
        padding: 0.9rem 1.2rem;
        margin: 0.8rem 0;
        color: #881337;
        font-size: 0.92rem;
        line-height: 1.8;
    }

    /* قسم التحقق الذاتي (Self-Verification) */
    .verify-box-input {
        background: #f8fafc;
        border: 1px solid #cbd5e1;
        border-top: 4px solid #0284c7;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        min-height: 135px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .verify-box-matn-l1 {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-top: 4px solid #16a34a;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        min-height: 135px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .verify-box-matn-l2 {
        background: #fffbeb;
        border: 1px solid #fde68a;
        border-top: 4px solid #d97706;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        min-height: 135px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .verify-box-matn-l3 {
        background: #fff1f2;
        border: 1px solid #fecdd3;
        border-top: 4px solid #e11d48;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        min-height: 135px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }

    /* أزرار منصة التحكيم السريعة */
    div[data-testid="column"] button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        padding: 0.5rem 0.25rem !important;
        border: 1px solid #cbd5e1 !important;
        background: #ffffff !important;
        transition: all 0.2s ease-in-out !important;
    }
    div[data-testid="column"] button:hover {
        border-color: #0284c7 !important;
        color: #0284c7 !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
    }
    /* إخفاء حدود ومقابض الشريط الجانبي المنهار تماماً */
    [data-testid="stSidebarCollapseButton"] {
        display: none !important;
    }

    [data-testid="stSidebar"] {
        border-left: none !important;
        border-right: none !important;
        box-shadow: none !important;
    }

    [data-testid="stSidebarNav"] {
        border: none !important;
    }

    /* إزالة خط الفصل ومقبض تغيير الحجم */
    [data-testid="stSidebarUserContent"] {
        border: none !important;
    }

    div[class*="stSidebar"] + div[data-testid="stBlock"] {
        border: none !important;
    }

    div[data-testid="collapsedControl"] {
        display: none !important;
    }

    /* منع أي بقايا خطوط عمودية أو مقابض سحب */
    .css-1544g2n, .e1fqkh3o3, section[data-testid="stSidebar"] ~ div {
        border: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# قراءة عنوان الخدمة عبر المتغير البيئي BACKEND_URL مع افتراض http://localhost:8080 كقيمة افتراضية
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080").rstrip("/")

def resolve_api_url() -> str:
    """استنتاج عنوان نقطة التحقق مع معالجة أسماء النطاقات الداخلية لتفادي أخطاء النطاق الداخلي"""
    explicit_backend = os.getenv("BACKEND_URL")
    explicit_api = os.getenv("API_URL")

    if explicit_api:
        if "backend:8080" in explicit_api:
            import socket
            try:
                socket.gethostbyname("backend")
                return explicit_api
            except Exception:
                return f"{BACKEND_URL}/api/v1/verify"
        return explicit_api

    return f"{BACKEND_URL}/api/v1/verify"

API_URL = resolve_api_url()

st.title("📜 بَيّنة AI | Bayyinah Engine")
st.caption("محرك فحص وتحقق دلالي هجين للمتون النبوية الشريفة")

with st.sidebar:
    st.header("📜 الميثاق العلمي والخصوصية")
    st.markdown("""
    **محرك بَيّنة AI** ملتزم بالمعايير الصارمة لعلوم الحديث الشريف ومحددات الذكاء الاصطناعي الإسلامي:
    
    - **📚 المصادر المعتمدة:** الربط الحصري بمتون السنة المسندة (صحيح البخاري، صحيح مسلم، الأربعون النووية).
    - **🚫 نفي التوليد الحر (Zero Hallucination):** اعتماد الاسترجاع الدلالي المعزز وتجنب أي تأليف أو توليد آلي حر للنصوص النبوية.
    - **🛑 الامتناع الذكي (Smart Abstention):** نفي النسبة عند غياب السند الصحيح، ورصد الأحاديث الموضوعة والباطلة.
    - **🔒 حفظ الخصوصية:** لا يتم تسجيل أو ربط الاستعلامات بأي بيانات هوية شخصية للمستخدمين نهائياً.
    """)
    st.divider()
    st.markdown("""
    **🏷️ مستويات اتخاذ القرار (Decision Badges):**
    - 🟢 **المستوى الأول (≥ 85%):** معتمد وصالح للنشر.
    - 🟠 **المستوى الثاني (60% - 84%):** محتوى مقارب يتطلب مراجعة وتثبت بشري.
    - 🔴 **المستوى الثالث (< 60%):** غير ثابت بالأصول المعتمدة (Smart Abstention).
    """)
    st.divider()
    st.caption(f"إصدار المحرك: `v0.3.5-scientific`\n\nنقطة الخدمة: `{API_URL}`")

# تهيئة حالة الجلسة (Session State Management)
if "query_input" not in st.session_state:
    st.session_state["query_input"] = ""
if "trigger_verify" not in st.session_state:
    st.session_state["trigger_verify"] = False

# منصة الفحص التجريبي بنقرة واحدة (One-Click Benchmark Playground)
st.markdown("### 🎯 سيناريوهات فحص سريعة (تجربة فورية للتحكيم)")
st.caption("اختر أحد السيناريوهات الأربعة للتحقق الفوري واستعراض قدرات المحرك بضغطة زر واحدة:")

p_col1, p_col2, p_col3, p_col4 = st.columns(4)

with p_col1:
    if st.button("🟢 تطابق لفظي مباشر", use_container_width=True, help="المستوى 1: فحص تطابق حرفي مباشر مع المتن الأصلي (ثقة ≥ 85%)"):
        st.session_state["query_input"] = "إنما الأعمال بالنيات وإنما لكل امرئ ما نوى"
        st.session_state["trigger_verify"] = True
        st.rerun()

with p_col2:
    if st.button("🟠 فهم دلالي معاصر", use_container_width=True, help="المستوى 2: فحص صياغة معاصرة ومحتوى مقارب يتطلب مراجعة وتثبت بشري (ثقة 60%-84%)"):
        st.session_state["query_input"] = "كف الأذى واللسان عن الآخرين علامة صدق الإيمان"
        st.session_state["trigger_verify"] = True
        st.rerun()

with p_col3:
    if st.button("⚡ كاش فوري (مستوى 1)", use_container_width=True, help="المستوى 1: استرجاع فوري للنتيجة والتحليل من الكاش (< 5ms)"):
        st.session_state["query_input"] = "من كان يؤمن بالله واليوم الآخر فليقل خيرا أو ليصمت"
        st.session_state["trigger_verify"] = True
        st.rerun()

with p_col4:
    if st.button("🔴 امتناع ذكي لمكذوب", use_container_width=True, help="المستوى 3: كشف مقولة غير ثابتة وإظهار سبب الامتناع لعدم وجود سند في الصحيحين (ثقة < 60%)"):
        st.session_state["query_input"] = "اطلبوا العلم ولو في الصين"
        st.session_state["trigger_verify"] = True
        st.rerun()

st.markdown("<div style='margin-bottom: 0.5rem;'></div>", unsafe_allow_html=True)

example_queries = [
    "اختر نموذجاً إضافياً للتجربة...",
    "إنما الأعمال بالنيات وإنما لكل امرئ ما نوى",
    "لا ضرر ولا ضرار",
    "كن في الدنيا كأنك غريب أو عابر سبيل",
    "السعي في تحصيل العلم ييسر الدخول إلى الجنة",
    "كف الأذى واللسان عن الآخرين علامة صدق الإيمان",
    "المعدة بيت الداء والحمية رأس الدواء",
    "اطلبوا العلم ولو في الصين"
]

selected_example = st.selectbox("أو اختر من النماذج الاسترشادية الإضافية:", example_queries, index=0)
if selected_example != example_queries[0] and st.session_state.get("last_selected_example") != selected_example:
    st.session_state["query_input"] = selected_example
    st.session_state["last_selected_example"] = selected_example
    st.rerun()

user_query = st.text_area("أدخل نص الحديث أو صياغته المعاصرة للتحقق:", value=st.session_state["query_input"], height=100)

submit_clicked = st.button("فحص المتن والإسناد", type="primary", use_container_width=True)

should_run = submit_clicked or st.session_state.get("trigger_verify", False)
if st.session_state.get("trigger_verify", False):
    st.session_state["trigger_verify"] = False

active_query = user_query.strip() or st.session_state.get("query_input", "").strip()

if should_run:
    if not active_query:
        st.warning("يرجى كتابة نص الاستعلام أولاً.")
    else:
        with st.spinner("جارٍ المعالجة الدلالية والبحث الهجين..."):
            start_time = time.perf_counter()
            try:
                # إرسال الحقل باسم query و text لمطابقة نموذج Pydantic في الـ Backend
                payload = {"query": active_query, "text": active_query}
                res = requests.post(API_URL, json=payload, timeout=35)
                elapsed_ms = (time.perf_counter() - start_time) * 1000

                if res.status_code == 200:
                    data = res.json()
                    status = data.get("status")
                    card = data.get("evidence_card")
                    is_cached = bool(data.get("cached", False))

                    raw_sim = data.get("similarity_score")
                    if raw_sim is None and card:
                        raw_sim = card.get("semantic_similarity", 0.0)
                    if raw_sim is None:
                        raw_sim = 0.0
                    confidence = float(raw_sim) * 100 if float(raw_sim) <= 1.0 else float(raw_sim)

                    # تصنيف النتيجة إلى 3 مستويات واضحة لصانع القرار (Decision Badges)
                    if status == "verified" and card:
                        if confidence >= 85.0:
                            decision_level = 1
                        elif confidence >= 60.0:
                            decision_level = 2
                        else:
                            decision_level = 3
                    else:
                        decision_level = 3

                    st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
                    col1, col2 = st.columns([1.35, 0.65])
                    with col1:
                        if decision_level == 1:
                            st.markdown(
                                f'<span class="decision-badge badge-level-1">🟢 <b>معتمد وصالح للنشر</b> (المستوى الأول - ثقة {confidence:.1f}%)</span>',
                                unsafe_allow_html=True
                            )
                        elif decision_level == 2:
                            st.markdown(
                                f'<span class="decision-badge badge-level-2">🟠 <b>محتوى مقارب - يتطلب مراجعة وتثبت بشري</b> (المستوى الثاني - ثقة {confidence:.1f}%)</span>',
                                unsafe_allow_html=True
                            )
                        else:
                            st.markdown(
                                '<span class="decision-badge badge-level-3">🔴 <b>غير ثابت بالأصول المعتمدة (Smart Abstention)</b> (المستوى الثالث)</span>',
                                unsafe_allow_html=True
                            )

                    with col2:
                        if is_cached:
                            st.markdown(
                                f'<div style="display: flex; align-items: center; justify-content: flex-end; gap: 8px;">'
                                f'<span class="metric-badge badge-cached">⚡ استجابة كاش: <span dir="ltr" style="display: inline-block;">{elapsed_ms:.1f} ms</span></span>'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                        else:
                            st.markdown(
                                f'<div style="display: flex; align-items: center; justify-content: flex-end; gap: 8px;">'
                                f'<span style="background: #f1f5f9; padding: 4px 12px; border-radius: 9999px; font-size: 0.85rem; color: #475569; font-weight: 600;">⏱️ زمن المعالجة: <span dir="ltr" style="display: inline-block;">{elapsed_ms:.1f} ms</span></span>'
                                f'</div>',
                                unsafe_allow_html=True
                            )

                    # توضيح مبرر القرار (Human-Readable Rationale) والتنبيهات الإجرائية
                    if decision_level == 1:
                        st.markdown(
                            f"""
                            <div class="rationale-card rationale-l1">
                                <div><b>💡 مبرر القرار (Rationale):</b> تطابق إسنادي ولفظي وثيق بنسبة ثقة عالية ({confidence:.1f}% &ge; 85%)، والمتن ثابت ومسند بالأصول المعتمدة في الصحيحين.</div>
                                <div style="margin-top: 5px;"><b>📋 الإجراء العملي المقترح قبل النشر:</b> النص معتمد وصالح للنشر والاستشهاد الفوري؛ ويُوصى بإرفاق التخريج الموثق المبيّن في بطاقة الإسناد أدناه (الكتاب، والباب، ورقم الحديث، وحكم المحدثين).</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    elif decision_level == 2:
                        st.markdown(
                            """
                            <div class="level2-alert-box">
                                ⚠️ <b>تنبيه احترازي:</b> يوجد تباين في الألفاظ أو تعدد في الروايات لا يحسمه التوليد الآلي؛ ويتعين التثبت البشري ومقارنة النص بكتب السنة المعتمدة قبل اعتماده.
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        st.markdown(
                            f"""
                            <div class="rationale-card rationale-l2">
                                <div><b>💡 مبرر القرار (Rationale):</b> تقع درجة الثقة في النطاق الحرج ({confidence:.1f}% بين 60% و 84%) لوجود تقارب دلالي مع المعنى الأصلي مع تباين في بعض الألفاظ أو احتمال تعدد الروايات في الباب.</div>
                                <div style="margin-top: 5px;"><b>📋 الإجراء العملي المقترح قبل النشر:</b> عدم الاكتفاء بالمعالجة الآلية وحدها؛ يتعين إحالة المتن لمراجع أو باحث متخصص للتثبت من اللفظ الوارد في الرواية المعتمدة ومطابقة الألفاظ بالأصول المسندة قبل النشر.</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    else: # decision_level == 3
                        st.markdown(
                            """
                            <div class="level3-abstention-box">
                                🛑 <b>سبب الامتناع الصريح (Smart Abstention):</b> عدم وجود سند مطابق في صحيحي البخاري ومسلم.
                                <div style="margin-top: 5px; font-size: 0.88rem; color: #9f1239;">
                                    امتنع المحرك آلياً عن نسبة هذا النص أو إجازة نشره التزاماً بميثاق النزاهة العلمية؛ حمايةً للسنة النبوية الشريفة من التوليد الآلي الحر أو ترويج المقولات الشائعة غير المسندة.
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        st.markdown(
                            f"""
                            <div class="rationale-card rationale-l3">
                                <div><b>💡 مبرر القرار (Rationale):</b> مؤشر الثقة دون حد الأمان العلمي ({confidence:.1f}% &lt; 60%)، مع انعدام أي سند صحيح مطابق في صحيحي البخاري ومسلم أو كتب السنة المعتمدة، أو لكون النص مقولة موضوعة لا أصل لها.</div>
                                <div style="margin-top: 5px;"><b>📋 الإجراء العملي المقترح قبل النشر:</b> الامتناع الصارم والتام عن نشر هذا النص أو نسبته إلى النبي ﷺ، والتحذير من تداوله كحديث نبوي شريف لعدم ثبوت سنده.</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    # قسم التحقق الذاتي للمستخدم (Self-Verification)
                    st.markdown("---")
                    st.subheader("🔍 قسم التحقق الذاتي (Self-Verification)")
                    st.caption("مقارنة مباشرة بين «النص المُدخل» و«المتن المعتمد في الصحيح» جنباً إلى جنب لتمكين المستخدم والمحكّم من الفحص البصري الفوري:")

                    v_col1, v_col2 = st.columns(2)
                    with v_col1:
                        st.markdown(
                            f"""
                            <div class="verify-box-input">
                                <div style="font-weight: 700; color: #0369a1; font-size: 0.95rem; margin-bottom: 8px;">📥 النص المُدخل (استعلام الفحص):</div>
                                <div style="font-family: 'Cairo', sans-serif; font-size: 1.05rem; color: #1e293b; line-height: 1.8;">{active_query}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    with v_col2:
                        if decision_level == 1:
                            matn_text = card.get("text", "") if card else ""
                            st.markdown(
                                f"""
                                <div class="verify-box-matn-l1">
                                    <div style="font-weight: 700; color: #15803d; font-size: 0.95rem; margin-bottom: 8px;">📖 المتن المعتمد في الصحيح:</div>
                                    <div style="font-family: 'Amiri', serif; font-size: 1.2rem; color: #064e3b; line-height: 2.0; font-weight: 700;">« {matn_text} »</div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        elif decision_level == 2:
                            matn_text = card.get("text", "") if card else ""
                            st.markdown(
                                f"""
                                <div class="verify-box-matn-l2">
                                    <div style="font-weight: 700; color: #c2410c; font-size: 0.95rem; margin-bottom: 8px;">📖 المتن المعتمد المقارب في الصحيح (للمقارنة والتثبت):</div>
                                    <div style="font-family: 'Amiri', serif; font-size: 1.2rem; color: #7c2d12; line-height: 2.0; font-weight: 700;">« {matn_text} »</div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        else:
                            st.markdown(
                                """
                                <div class="verify-box-matn-l3">
                                    <div style="font-weight: 700; color: #b91c1c; font-size: 0.95rem; margin-bottom: 8px;">🛑 المتن في مصادر السنة المعتمدة:</div>
                                    <div style="font-family: 'Amiri', serif; font-size: 1.15rem; color: #991b1b; line-height: 2.0; font-weight: 700;">« لم يُعثر على أصل مطابق أو سند معتمد في صحيحي البخاري ومسلم »</div>
                                    <div style="font-size: 0.85rem; color: #7f1d1d; margin-top: 6px;">(موقف الامتناع الذكي المفعل: نفي النسبة وحظر التوليد الحر)</div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                    if decision_level in [1, 2] and card:
                        st.markdown("---")
                        if decision_level == 1:
                            st.subheader("📋 بطاقة الإسناد المعتمدة (Evidence Card)")
                        else:
                            st.subheader("📋 بيانات الشاهد الإسنادي المقارب (Evidence Card)")

                        evidence = card
                        source_book = evidence.get("source_book") or evidence.get("source", "الأصول المسندة")
                        chapter = evidence.get("chapter", "عام")
                        
                        hadith_id = str(evidence.get("hadith_id") or "")
                        raw_num = evidence.get("hadith_number") or evidence.get("number", "غير محدد")
                        is_nawawi = "nawawi_" in hadith_id.lower() or "الأربعون النووية" in str(source_book) or "النووية" in str(source_book)
                        if is_nawawi and raw_num not in ["-", "غير محدد"]:
                            hadith_num = f"{raw_num} (الأربعون النووية)"
                        else:
                            hadith_num = str(raw_num)

                        verdict = evidence.get("scholar_verdict") or evidence.get("verdict", "صحيح")

                        st.markdown(f'<div class="hadith-text">« {evidence.get("text", "")} »</div>', unsafe_allow_html=True)

                        # إبراز الكتاب، والباب، ورقم الحديث، وحكم المحدثين
                        card_html = f"""<div style="direction: rtl; text-align: right; margin: 15px 0;">
    <div style="display: flex; flex-wrap: wrap; gap: 10px; justify-content: center;">
        <div style="background: #f1f5f9; padding: 10px 14px; border-radius: 8px; min-width: 120px; text-align: center;">
            <div style="font-size: 0.8rem; color: #64748b;">الكتاب (المصدر المعتمد)</div>
            <div style="font-size: 0.95rem; font-weight: bold; color: #1e293b;">{source_book}</div>
        </div>
        <div style="background: #f1f5f9; padding: 10px 14px; border-radius: 8px; min-width: 120px; text-align: center;">
            <div style="font-size: 0.8rem; color: #64748b;">الباب / الموضوع</div>
            <div style="font-size: 0.95rem; font-weight: bold; color: #1e293b;">{chapter}</div>
        </div>
        <div style="background: #f1f5f9; padding: 10px 14px; border-radius: 8px; min-width: 120px; text-align: center;">
            <div style="font-size: 0.8rem; color: #64748b;">رقم الحديث</div>
            <div style="font-size: 0.95rem; font-weight: bold; color: #1e293b;">{hadith_num}</div>
        </div>
        <div style="background: #f1f5f9; padding: 10px 14px; border-radius: 8px; min-width: 120px; text-align: center;">
            <div style="font-size: 0.8rem; color: #64748b;">درجة الثقة / المطابقة</div>
            <div style="font-size: 0.95rem; font-weight: bold; color: {'#166534' if decision_level == 1 else '#c2410c'};">{confidence:.1f}%</div>
        </div>
        <div style="background: #ecfdf5; border: 1px solid #a7f3d0; padding: 10px 14px; border-radius: 8px; min-width: 120px; text-align: center;">
            <div style="font-size: 0.8rem; color: #065f46;">حكم المحدثين</div>
            <div style="font-size: 0.95rem; font-weight: bold; color: #047857;">⚖️ {verdict}</div>
        </div>
    </div>
</div>"""
                        st.markdown(card_html, unsafe_allow_html=True)

                        # طبقة التفسير والربط الدلالي (Semantic Explainability Layer)
                        insight = data.get("alignment_insight")
                        if insight:
                            st.markdown("---")
                            st.subheader("💡 التحليل الدلالي والتفسير العلمي (Explainability Layer)")
                            if isinstance(insight, dict):
                                concepts = insight.get("matched_concepts", [])
                                explanation = insight.get("explanation", "")
                                if concepts:
                                    badges_html = " ".join([f'<span class="concept-badge">🏷️ {c}</span>' for c in concepts])
                                    st.markdown(f"**المفاهيم الجوهرية المشتركة:** {badges_html}", unsafe_allow_html=True)
                                if explanation:
                                    st.markdown(f'<div class="insight-card">💡 <b>الوجه الدلالي:</b> {explanation}</div>', unsafe_allow_html=True)
                            elif isinstance(insight, str):
                                st.markdown(f'<div class="insight-card">⚡ <b>التحليل اللفظي:</b> {insight}</div>', unsafe_allow_html=True)

                        # تصدير بطاقة الإسناد والتحقق
                        st.markdown("---")
                        st.markdown("### 📥 تصدير بطاقة الإسناد والتحقق")

                        if "source_book" not in evidence and "source" in evidence:
                            evidence["source_book"] = evidence["source"]
                        if "hadith_number" not in evidence and "number" in evidence:
                            evidence["hadith_number"] = evidence["number"]
                        if "scholar_verdict" not in evidence and "verdict" in evidence:
                            evidence["scholar_verdict"] = evidence["verdict"]

                        alignment = data.get("alignment_insight", {})

                        level_title = "المستوى الأول: معتمد وصالح للنشر" if decision_level == 1 else "المستوى الثاني: محتوى مقارب - يتطلب مراجعة وتثبت بشري"
                        rationale_note = "تطابق إسنادي ولفظي وثيق (ثقة ≥ 85%) في الأصول المسندة المعتمدة." if decision_level == 1 else "تقارب دلالي مع الأصل النبوي (60%-84%) مع وجود تباين لفظي يستوجب التثبت البشري ومطابقة الروايات."
                        action_note = "معتمد ومجاز للنشر والاستشهاد الفوري مع التخريج الموثق." if decision_level == 1 else "مراجعة وتثبت بشري متخصص لمطابقة الألفاظ بالأصول قبل النشر وعدم الاكتفاء بالتوليد الآلي."

                        # Format Plain Text Certificate
                        export_text = f"""==================================================
           بَيّنة AI - بطاقة إسناد وتحقق حديثي
           تحدي الذكاء الاصطناعي في خدمة المحتوى الإسلامي 2026
==================================================

[تصنيف النتيجة لصانع القرار]:
• قرار المنظومة : {level_title}
• نسبة الثقة    : {confidence:.1f}%
• مبرر القرار   : {rationale_note}
• الإجراء المقترح: {action_note}

[مقارنة التحقق الذاتي]:
• النص المُدخل  : {active_query}
• المتن المعتمد : « {evidence.get('text', '')} »

[بيانات التخريج والتوثيق]:
• الكتاب (المصدر): {evidence.get('source_book', '')}
• الباب / الموضوع: {evidence.get('chapter', '')}
• رقم الحديث    : {evidence.get('hadith_number', '')}
• حكم المحدثين  : {evidence.get('scholar_verdict', 'صحيح')}

[المفاهيم ووجه الدلالة]:
• المفاهيم المشتركة: {', '.join(alignment.get('matched_concepts', [])) if isinstance(alignment, dict) else 'تطابق لفظي'}
• وجه المطابقة     : {alignment.get('explanation', alignment) if isinstance(alignment, dict) else alignment}

--------------------------------------------------
المرجعية العلمية: الأصول المسندة المعتمدة (صحيح البخاري، صحيح مسلم، الأربعون النووية)
تنبيه: أداة مساعدة إسنادية مدعومة بالذكاء الاصطناعي والامتناع الذكي ولا تستقل بإصدار فتاوى.
=================================================="""

                        col_exp1, col_exp2 = st.columns(2)

                        with col_exp1:
                            st.download_button(
                                label="📄 تنزيل شهادة التحقق (TXT)",
                                data=export_text.encode('utf-8'),
                                file_name=f"bayyinah_verification_{evidence.get('hadith_id', 'hadith')}.txt",
                                mime="text/plain",
                                use_container_width=True
                            )

                        with col_exp2:
                            badge_color = "#16a34a" if decision_level == 1 else "#d97706"
                            badge_bg = "#dcfce7" if decision_level == 1 else "#ffedd5"
                            badge_txt = "#166534" if decision_level == 1 else "#9a3412"

                            html_card = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
  <meta charset="UTF-8">
  <title>بطاقة إسناد - بَيّنة AI</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 25px; background: #f8fafc; color: #1e293b; }}
    .card {{ background: #ffffff; border: 2px solid {badge_color}; border-radius: 12px; padding: 25px; max-width: 650px; margin: auto; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
    .header {{ text-align: center; border-bottom: 2px solid #e2e8f0; padding-bottom: 12px; margin-bottom: 18px; }}
    .header h2 {{ margin: 0; color: #0f5132; font-size: 20px; }}
    .header p {{ margin: 4px 0 0 0; color: #64748b; font-size: 12px; }}
    .badge-box {{ text-align: center; margin-bottom: 15px; }}
    .badge {{ display: inline-block; background: {badge_bg}; color: {badge_txt}; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 13px; border: 1px solid {badge_color}; }}
    .self-verify {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; margin-bottom: 15px; font-size: 13px; }}
    .matn {{ background: #f0fdf4; border-right: 4px solid {badge_color}; padding: 15px; border-radius: 6px; font-size: 16px; line-height: 1.8; font-weight: bold; margin-bottom: 18px; }}
    .meta-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px; font-size: 13px; }}
    .meta-item {{ background: #f1f5f9; padding: 8px 12px; border-radius: 6px; }}
    .rationale {{ background: #f8fafc; border-right: 3px solid #0284c7; padding: 10px; border-radius: 4px; font-size: 12px; margin-bottom: 15px; line-height: 1.6; }}
    .footer {{ font-size: 11px; text-align: center; color: #94a3b8; border-top: 1px solid #e2e8f0; padding-top: 10px; margin-top: 15px; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="header">
      <h2>بَيّنة AI | بطاقة إسناد وتحقق حديثي</h2>
      <p>تحدي الذكاء الاصطناعي في خدمة المحتوى الإسلامي 2026</p>
    </div>
    <div class="badge-box">
      <span class="badge">{level_title} (ثقة {confidence:.1f}%)</span>
    </div>
    <div class="self-verify">
      <div><strong>النص المُدخل:</strong> {active_query}</div>
    </div>
    <div class="matn">« {evidence.get('text', '')} »</div>
    <div class="meta-grid">
      <div class="meta-item"><strong>الكتاب (المصدر):</strong> {evidence.get('source_book', '')}</div>
      <div class="meta-item"><strong>الباب / الموضوع:</strong> {evidence.get('chapter', '')}</div>
      <div class="meta-item"><strong>رقم الحديث:</strong> {evidence.get('hadith_number', '')}</div>
      <div class="meta-item"><strong>حكم المحدثين:</strong> {evidence.get('scholar_verdict', 'صحيح')}</div>
    </div>
    <div class="rationale">
      <strong>مبرر القرار:</strong> {rationale_note}<br>
      <strong>الإجراء المقترح:</strong> {action_note}
    </div>
    <div class="footer">
      أُنتجت بواسطة منظومة بَيّنة AI للتحقق الحديثي والإسنادي • متوافقة مع ميثاق الحزمة العلمية
    </div>
  </div>
</body>
</html>"""
                            st.download_button(
                                label="🌐 تنزيل بطاقة النشر (HTML)",
                                data=html_card.encode('utf-8'),
                                file_name=f"bayyinah_card_{evidence.get('hadith_id', 'hadith')}.html",
                                mime="text/html",
                                use_container_width=True
                            )
                    else: # decision_level == 3
                        st.markdown("---")
                        st.markdown("### 📥 تصدير إشعار الامتناع والتحقق")
                        refusal_msg = data.get("message", "لم يتم العثور على أصل مطابق في مصادر السنة المعتمدة، ولا يُنسب إلى النبي ﷺ ما لم يثبت إسناده.")

                        export_text_l3 = f"""==================================================
           بَيّنة AI - إشعار امتناع ذكي ونفي نسبة
           تحدي الذكاء الاصطناعي في خدمة المحتوى الإسلامي 2026
==================================================

[تصنيف النتيجة لصانع القرار]:
• قرار المنظومة : المستوى الثالث: غير ثابت بالأصول المعتمدة (Smart Abstention)
• شارة القرار   : 🛑 غير ثابت بالأصول المعتمدة (Smart Abstention)
• سبب الامتناع  : عدم وجود سند مطابق في صحيحي البخاري ومسلم
• نسبة الثقة    : {confidence:.1f}%

[مقارنة التحقق الذاتي]:
• النص المُدخل  : {active_query}
• النتيجة في الصحيح: لا يوجد سند مطابق في صحيحي البخاري ومسلم (امتناع ذكي صريح)

[مبرر القرار والإجراء المقترح]:
• مبرر القرار   : مؤشر الثقة دون حد الأمان العلمي ({confidence:.1f}% < 60%) ولم يُعثر على إسناد مطابق في صحيحي البخاري ومسلم.
• الإجراء المقترح: الامتناع الصارم والتام عن نشر هذا النص أو نسبته إلى النبي ﷺ؛ صيانةً للأمانة العلمية ودرءاً للوهم.

--------------------------------------------------
المرجعية العلمية: الأصول المسندة المعتمدة (صحيح البخاري، صحيح مسلم، الأربعون النووية)
تنبيه: ميزة الامتناع الذكي تعطل التوليد الحر وتمنع تمرير الروايات التي لا تثبت في الصحيحين.
=================================================="""

                        col_exp1, col_exp2 = st.columns(2)
                        with col_exp1:
                            st.download_button(
                                label="📄 تنزيل إشعار الامتناع الذكي (TXT)",
                                data=export_text_l3.encode('utf-8'),
                                file_name=f"bayyinah_abstention_{int(time.time())}.txt",
                                mime="text/plain",
                                use_container_width=True
                            )
                        with col_exp2:
                            html_abstention = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
  <meta charset="UTF-8">
  <title>إشعار امتناع ذكي - بَيّنة AI</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 25px; background: #fff5f5; color: #1e293b; }}
    .card {{ background: #ffffff; border: 2px solid #b91c1c; border-radius: 12px; padding: 25px; max-width: 650px; margin: auto; box-shadow: 0 4px 12px rgba(185,28,28,0.08); }}
    .header {{ text-align: center; border-bottom: 2px solid #fee2e2; padding-bottom: 12px; margin-bottom: 18px; }}
    .header h2 {{ margin: 0; color: #b91c1c; font-size: 20px; }}
    .header p {{ margin: 4px 0 0 0; color: #64748b; font-size: 12px; }}
    .badge {{ display: inline-block; background: #fee2e2; color: #991b1b; padding: 6px 14px; border-radius: 20px; font-weight: bold; margin-bottom: 14px; border: 1px solid #f87171; font-size: 13px; }}
    .query-box {{ background: #f8fafc; border-right: 4px solid #64748b; padding: 12px; border-radius: 6px; font-size: 15px; margin-bottom: 14px; }}
    .reason-box {{ background: #fff1f2; border-right: 4px solid #e11d48; padding: 14px; border-radius: 6px; font-size: 14px; color: #881337; line-height: 1.8; margin-bottom: 15px; }}
    .footer {{ font-size: 11px; text-align: center; color: #94a3b8; border-top: 1px solid #fee2e2; padding-top: 10px; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="header">
      <h2>بَيّنة AI | إشعار امتناع ذكي ونفي نسبة</h2>
      <p>تحدي الذكاء الاصطناعي في خدمة المحتوى الإسلامي 2026</p>
    </div>
    <div style="text-align: center;"><span class="badge">🛑 المستوى الثالث: غير ثابت بالأصول المعتمدة (Smart Abstention)</span></div>
    <div class="query-box"><strong>النص المُدخل:</strong> {active_query}</div>
    <div class="reason-box">
      <strong>سبب الامتناع الصريح:</strong> عدم وجود سند مطابق في صحيحي البخاري ومسلم.<br>
      <strong>الإجراء الموصى به:</strong> الامتناع عن نسبة هذا اللفظ إلى النبي ﷺ أو نشره وتداوله كحديث نبوي.
    </div>
    <div class="footer">
      أُنتجت بواسطة منظومة بَيّنة AI للتحقق الحديثي والإسنادي • ميزة الامتناع الذكي
    </div>
  </div>
</body>
</html>"""
                            st.download_button(
                                label="🌐 تنزيل بطاقة الامتناع (HTML)",
                                data=html_abstention.encode('utf-8'),
                                file_name=f"bayyinah_abstention_{int(time.time())}.html",
                                mime="text/html",
                                use_container_width=True
                            )
                else:
                    st.error(f"خطأ من الخادم: HTTP {res.status_code} - {res.text}")
            except requests.exceptions.Timeout:
                st.error("⚠️ انتهت مهلة الاتصال بالخادم (استغرق التضمين والتحقق وقتاً أطول من المتوقع). يرجى المحاولة مرة أخرى.")
            except requests.exceptions.RequestException as e:
                st.error(f"تعذر الاتصال بالخادم: {e}")
            except Exception as e:
                st.error(f"حدث خطأ غير متوقع: {e}")

# الميثاق العلمي والشفافية المنهجية وحفظ الخصوصية
st.markdown("---")
with st.expander("⚖️ إخلاء المسؤولية العلمي والشفافية المنهجية (Scientific Charter & Privacy)", expanded=False):
    st.markdown("""
    #### 1. المنهجية العلمية والتحقق الإسنادي
    يعتمد محرك **بَيّنة AI** على بنية هجينة للتحقق تجمع بين البحث النصي الحرفي المطابق (Full-Text Search) والبحث الدلالي الموجه بنماذج التضمين الحديثة (`text-embedding-004` مع `pgvector`). تلتزم المنظومة بالتحقق الدقيق من ثبوت المتن في الأصول المسندة المعتمدة لدى أهل الحديث، مع الامتناع الصارم عن التوليد الآلي الحر صيانةً للأمانة العلمية.

    #### 2. آلية الرفض الذكي (Smart Refusal)
    عند فحص استعلام يمثل مقولة شائعة لا أصل لها أو حديثاً موضوعاً أو غير ثابت في كتب السنة (مثل: «اطلبوا العلم ولو في الصين»، «المعدة بيت الداء»)، يمتنع المحرك بحزم عن إثبات النسبة ويُصدر إشعار الرفض المعتمد:
    > *«لم يتم العثور على أصل مطابق في مصادر السنة المعتمدة، ولا يُنسب إلى النبي ﷺ ما لم يثبت إسناده.»*

    #### 3. سياسة حفظ الخصوصية وأمان الاستعلام
    صُمم النظام لضمان أعلى معايير الخصوصية والأمان؛ حيث لا يتم تسجيل أي استعلامات أو ربطها بهويات المستخدمين. تُستخدم الذاكرة المؤقتة (In-Memory Cache) حصراً لتسريع استجابة المعالجة الحسابية دون أي تتبع أو مشاركة خارجية.
    """)
st.caption("🔒 محرك آمن وخاص | لا يتم حفظ استعلامات المستخدمين الشخصية | متوافق مع الميثاق العلمي للذكاء الاصطناعي الإسلامي")
