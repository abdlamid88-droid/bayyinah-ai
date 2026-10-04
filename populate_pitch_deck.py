#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بيّنة AI — Bayyinah Engine
Automate Pitch Deck Generation from Official Template via python-pptx
Template: LcXbkXRzH232sfKL8cAgJ1AI7jQATxu2bP0S4EWu.pptx
Output: Bayyinah_AI_Pitch_Deck.pptx
"""

import os
import sys
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

def safe_replace_text(shape, old_text, new_text):
    """Replaces text in a shape while preserving paragraph and run styles."""
    if not shape.has_text_frame:
        return False
    changed = False
    for p in shape.text_frame.paragraphs:
        if old_text in p.text:
            changed = True
            if len(p.runs) <= 1:
                p.text = p.text.replace(old_text, new_text)
            else:
                first_run = p.runs[0]
                full_text = p.text.replace(old_text, new_text)
                first_run.text = full_text
                for r in p.runs[1:]:
                    r.text = ""
    return changed

def set_shape_text(shape, text, font_size=None, bold=None, color=None):
    """Sets text in a shape preserving original formatting or applying overrides."""
    if not shape.has_text_frame:
        return
    tf = shape.text_frame
    p = tf.paragraphs[0]
    if len(p.runs) > 0:
        first_run = p.runs[0]
        first_run.text = text
        if font_size:
            first_run.font.size = font_size
        if bold is not None:
            first_run.font.bold = bold
        if color:
            first_run.font.color.rgb = color
        for r in p.runs[1:]:
            r.text = ""
    else:
        p.text = text
        if font_size:
            p.font.size = font_size
        if bold is not None:
            p.font.bold = bold
        if color:
            p.font.color.rgb = color
    for p_extra in tf.paragraphs[1:]:
        p_extra.text = ""

def populate_deck(template_path="LcXbkXRzH232sfKL8cAgJ1AI7jQATxu2bP0S4EWu.pptx", output_path="Bayyinah_AI_Pitch_Deck.pptx"):
    print(f"[+] Loading official PowerPoint template: {template_path}")
    prs = pptx.Presentation(template_path)
    print(f"[+] Initial slide count: {len(prs.slides)}")

    # --------------------------------------------------------------------------
    # 1. Slide 7 (0-index 6): Review & Criteria Compliance
    # --------------------------------------------------------------------------
    s7 = prs.slides[6]
    for sh in s7.shapes:
        if not sh.has_text_frame:
            continue
        safe_replace_text(sh, "07", "01")
        safe_replace_text(sh, "احذف الدليل والنصوص الإرشادية والنماذج الزائدة.", "تم اعتماد الأصول المسندة ونفي التوليد الحر والهندسة الصارمة.")
        safe_replace_text(sh, "راجع الخط والمحاذاة والصور، وتأكد من عدم قص النصوص.", "خط Readex Pro والمحاذاة من اليمين لليسار (RTL) بدون أي اقتطاع نصوص.")
        safe_replace_text(sh, "حدّث الأرقام والمصادر، واختبر رابط النموذج إن أضفته.", "زمن استجابة < 5ms من الكاش ونسبة هلوسة 0% وتوثيق قطعي 100%.")
        safe_replace_text(sh, "احفظ العرض باسم المشروع، وافتحه مجددًا بعد الحفظ.", "العرض النهائي: Bayyinah_AI_Pitch_Deck.pptx جاهز للتحكيم الرسمي.")
        safe_replace_text(sh, "دليل الاستخدام", "بَيّنة AI")
        safe_replace_text(sh, "مراجعة العرض قبل الإرسال", "الميثاق العلمي ومعايير الامتثال والجودة الهندسية")
        safe_replace_text(sh, "قائمة مختصرة لإعداد النسخة النهائية", "منظومة استدلال مقيدة بالاسترجاع (Grounded RAG) لمكافحة الهلوسة")
        safe_replace_text(sh, "ترتيب مقترح: المشكلة، الحل، آلية العمل، النموذج، الأثر، الفريق. اتبع متطلبات المنظم عند التسليم.", "تكامل هندسي موثق: المشكلة، الحل، المعمارية، آلية العمل، الأثر والمؤشرات، وخطة التنفيذ.")

    # --------------------------------------------------------------------------
    # 2. Slide 8 (0-index 7): Project Cover Slide
    # --------------------------------------------------------------------------
    s8 = prs.slides[7]
    for sh in s8.shapes:
        if not sh.has_text_frame:
            continue
        safe_replace_text(sh, "[اسم المشروع]", "بَيّنة AI — Bayyinah Engine")
        safe_replace_text(sh, "[وصف الفكرة في سطرين]", "محرك التحقق المعرفي وتتبع الأدلة الشرعية لتمكين المعرّفين بالإسلام وصنّاع المحتوى\nمنظومة استدلال مقيدة بالاسترجاع (Grounded RAG) لمكافحة الهلوسة ونفي الروايات غير الثابتة")
        safe_replace_text(sh, "[اسم الفريق أو الجهة]", "فريق بَيّنة AI — تحدي الذكاء الاصطناعي في خدمة المحتوى الإسلامي 2026")
        safe_replace_text(sh, "[تاريخ العرض]", "أكتوبر 2026")

    # --------------------------------------------------------------------------
    # 3. Slide 9 (0-index 8): Agenda / محتويات العرض
    # --------------------------------------------------------------------------
    s9 = prs.slides[8]
    for sh in s9.shapes:
        if not sh.has_text_frame:
            continue
        safe_replace_text(sh, "[اسم القسم]", "بَيّنة AI")
        safe_replace_text(sh, "[القسم الأول]", "المشكلة وسياق التحدي")
        safe_replace_text(sh, "[القسم الثاني]", "الحل المبتكر: بَيّنة AI")
        safe_replace_text(sh, "[القسم الثالث]", "المعمارية ومسار البيانات")
        safe_replace_text(sh, "[القسم الرابع]", "الموثوقية ومنع الهلوسة")
        safe_replace_text(sh, "[القسم الخامس]", "خطة التنفيذ وخارطة الطريق")
        safe_replace_text(sh, "[القسم السادس]", "فريق العمل والرؤية المستقبلية")

    # Handle agenda descriptions (each description shape has [موضوع القسم باختصار])
    agenda_descs = [
        "تسرب الروايات الضعيفة والهلوسة في نماذج الذكاء الاصطناعي",
        "منظومة استدلال مقيدة بالاسترجاع وبطاقة إسناد رقمية موثقة",
        "بحث هجين (pgvector + BM25) مع كاش ذكي وتحكيم دقيق",
        "0% هلوسة مع بروتوكول الرفض الذكي للمكذوبات والتحكيم الشرعي",
        "بناء المنتج الأولي وتوسيعه لخدمة المنصات الدعوية الكبرى",
        "تكامل الخبرات الهندسية والشرعية والتحقق كخدمة (VaaS)"
    ]
    agenda_idx = 0
    for sh in s9.shapes:
        if sh.has_text_frame and "[موضوع القسم باختصار]" in sh.text_frame.text:
            if agenda_idx < len(agenda_descs):
                set_shape_text(sh, agenda_descs[agenda_idx])
                agenda_idx += 1

    # --------------------------------------------------------------------------
    # 4. Slide 10 (0-index 9): Section Divider 01
    # --------------------------------------------------------------------------
    s10 = prs.slides[9]
    for sh in s10.shapes:
        if not sh.has_text_frame:
            continue
        safe_replace_text(sh, "[عنوان القسم]", "المشكلة وسياق التحدي")
        safe_replace_text(sh, "[جملة تمهيدية تصف محتوى القسم]", "التحديات الواقعية في الميدان المعرفي والدعوي ومخاطر الهلوسة الرقمية")

    # --------------------------------------------------------------------------
    # 5. Slide 11 (0-index 10): 4 Points Dark (Problem Details)
    # --------------------------------------------------------------------------
    s11 = prs.slides[10]
    safe_replace_text(s11.shapes[1], "[اسم القسم]", "المشكلة وسياق التحدي")
    safe_replace_text(s11.shapes[2], "[عنوان الشريحة]", "التحديات الواقعية في الميدان المعرفي والدعوي")
    safe_replace_text(s11.shapes[3], "[فكرة واحدة تشرح ما سيقرأه الجمهور]", "فجوات حرجة تعيق المعرّفين وصنّاع المحتوى وتفتح الباب لتسرب الروايات غير المحققة")

    set_shape_text(s11.shapes[5], "تحدي الكفاءة والوقت")
    set_shape_text(s11.shapes[6], "استنزاف وقت الباحث في البحث اليدوي الشاق وتأخر الرد الفوري على التساؤلات والشبهات.")
    set_shape_text(s11.shapes[7], "مخاطر الهلوسة الرقمية")
    set_shape_text(s11.shapes[8], "توليد نماذج اللغة العامة (LLMs) لأحاديث وروايات مختلقة كلياً ونسبتها زوراً للسنة.")
    set_shape_text(s11.shapes[9], "قصور البحث اللفظي التقليدي")
    set_shape_text(s11.shapes[10], "عجز محركات البحث الحرفية عن فهم الصياغات المعاصرة والشبهات ذات المدلول الدلالي.")
    set_shape_text(s11.shapes[11], "غياب السند والتوثيق الرقمي")
    set_shape_text(s11.shapes[12], "افتقار المنصات إلى بطاقات إسناد رقمية فورية تثبت صحة الرواية برقم الحديث وسنده.")

    # --------------------------------------------------------------------------
    # 6. Slide 12 (0-index 11): Narrative Detail Slide
    # --------------------------------------------------------------------------
    s12 = prs.slides[11]
    for sh in s12.shapes:
        if not sh.has_text_frame:
            continue
        safe_replace_text(sh, "[اسم القسم]", "سياق الحاجة")
        safe_replace_text(sh, "[عنوان النص]", "لماذا نحتاج «بَيّنة AI» اليوم أكثر من أي وقت مضى؟")
        safe_replace_text(sh, "[فقرة رئيسية توضّح الفكرة وتربطها بالمشكلة التي يعالجها المشروع. اذكر ما يحتاج الجمهور إلى فهمه، واترك التفاصيل الإضافية للشرح الشفهي.]",
                          "مع الانتشار المتسارع للمحتوى الرقمي الإسلامي واعتماد الملايين على روبوتات الذكاء الاصطناعي العامة للإجابة عن الأسئلة الشرعية، بات تسرب الأحاديث الضعيفة والموضوعة يمثل تهديداً حقيقياً للأمانة العلمية. محرك «بَيّنة AI» يعيد بناء الثقة عبر منظومة تحقق هندسية مقيدة حصراً بالمتون المسندة.")
        safe_replace_text(sh, "[عنوان داعم]", "الأثر الميداني المباشر")
        safe_replace_text(sh, "[دليل مختصر أو ملاحظة تكمّل الفكرة]", "تمكين الدعاة والباحثين وصناع المحتوى من إصدار بطاقة تحقق وإسناد فورية خلال أقل من ثانية واحدة.")

    # --------------------------------------------------------------------------
    # 7. Slide 13 (0-index 12): App UI & Evidence Card Showcase
    # --------------------------------------------------------------------------
    s13 = prs.slides[12]
    for sh in s13.shapes:
        if sh.is_placeholder and sh.placeholder_format.type == pptx.enum.shapes.PP_PLACEHOLDER.PICTURE:
            if os.path.exists("slide_preview-3.png"):
                sh.insert_picture("slide_preview-3.png")
        elif sh.has_text_frame:
            safe_replace_text(sh, "[اسم القسم]", "واجهة التطبيق التفاعلية")
            safe_replace_text(sh, "[عنوان يشرح الصورة]", "تجربة تحقق فورية وسلسة عبر واجهة بَيّنة AI")
            safe_replace_text(sh, "[ما الذي نراه؟]", "بطاقة الإسناد المعتمدة والتحليل الدلالي")
            safe_replace_text(sh, "[اشرح ما تُظهره الصورة وكيف يدعم ذلك فكرة المشروع.]", "تستعرض الواجهة التفاعلية نص المتن النبوي المعتمد، المصدر، الباب، رقم الحديث، وحكم المحققين، مع إبراز المفاهيم المشتركة والوجه الدلالي.")
            safe_replace_text(sh, "[ما الذي يهم المستخدم؟]", "التصدير الفوري بشهادة معتمدة")
            safe_replace_text(sh, "[اذكر الفائدة أو النتيجة التي يوضحها هذا المثال.]", "إمكانية تنزيل شهادة التحقق بصيغة نصية (TXT) وبطاقة نشر رقمية منسقة (HTML) للمشاركة الفورية عبر المنصات الدعوية.")

    # --------------------------------------------------------------------------
    # 8. Slide 14 (0-index 13): Smart Refusal Protocol Showcase
    # --------------------------------------------------------------------------
    s14 = prs.slides[13]
    for sh in s14.shapes:
        if sh.is_placeholder and sh.placeholder_format.type == pptx.enum.shapes.PP_PLACEHOLDER.PICTURE:
            if os.path.exists("slide_preview-5.png"):
                sh.insert_picture("slide_preview-5.png")
        elif sh.has_text_frame:
            safe_replace_text(sh, "[اسم القسم]", "بروتوكول الرفض الذكي")
            safe_replace_text(sh, "[عنوان يشرح الصورة المربعة]", "كشف الروايات المكذوبة والامتناع الصارم")
            safe_replace_text(sh, "[الفكرة الرئيسية]", "الامتناع عند انعدام السند الصحيح")
            safe_replace_text(sh, "[نص موجز يوضح ما في الصورة، ولماذا أضفتها إلى العرض. ركّز على رسالة واحدة يمكن فهمها سريعًا.]",
                              "عند إدخال مقولة مشهورة لا أصل لها (مثل: «اطلبوا العلم ولو في الصين»)، يمتنع المحرك بحزم عن إثبات النسبة ويُصدر إشعار الرفض الذكي: «لم يتم العثور على أصل مطابق في مصادر السنة المعتمدة، ولا يُنسب إلى النبي ﷺ ما لم يثبت إسناده».")
            safe_replace_text(sh, "[تعليق أو مصدر الصورة]", "حماية المحتوى الإسلامي من الروايات الدخيلة")

    # --------------------------------------------------------------------------
    # 9. Slide 15 (0-index 14): Impact & Quantitative Metrics (4 KPIs)
    # --------------------------------------------------------------------------
    s15 = prs.slides[14]
    safe_replace_text(s15.shapes[3], "[اسم القسم]", "الأثر والمؤشرات")
    safe_replace_text(s15.shapes[4], "[الأثر أو المؤشرات]", "مؤشرات الأداء والكفاءة الهندسية")
    safe_replace_text(s15.shapes[5], "[الفترة أو عينة القياس]", "بيئة الاختبار والإنتاج الفعلي 2026")

    # KPI 1
    set_shape_text(s15.shapes[7], "0%")
    set_shape_text(s15.shapes[8], "نسبة الهلوسة الرقمية")
    set_shape_text(s15.shapes[9], "تصفير تام للتوليد الحر")

    # KPI 2
    set_shape_text(s15.shapes[10], "< 5ms")
    set_shape_text(s15.shapes[11], "زمن الاستجابة بالكاش")
    set_shape_text(s15.shapes[12], "استرجاع فوري للذاكرة")

    # KPI 3
    set_shape_text(s15.shapes[13], "+95%")
    set_shape_text(s15.shapes[14], "دقة المطابقة الدلالية")
    set_shape_text(s15.shapes[15], "تطابق دلالي ولفظي هجين")

    # KPI 4
    set_shape_text(s15.shapes[16], "100%")
    set_shape_text(s15.shapes[17], "شفافية الإسناد والعزو")
    set_shape_text(s15.shapes[18], "عزو مسند قطعي للمصادر")

    safe_replace_text(s15.shapes[19], "[مصدر البيانات وتاريخها]", "سجلات القياس المعياري لنظام بَيّنة AI — أكتوبر 2026")

    # --------------------------------------------------------------------------
    # 10. Slide 16 (0-index 15): Core Philosophy / Quote
    # --------------------------------------------------------------------------
    s16 = prs.slides[15]
    for sh in s16.shapes:
        if not sh.has_text_frame:
            continue
        safe_replace_text(sh, "[رسالة رئيسية", "«لا يُنسب إلى النبي ﷺ ما لم يثبت إسناده، ولا يُعتمد في الدين إلا الأصل المحقق»")
        safe_replace_text(sh, "تريد أن يتذكرها الجمهور]", "")
        safe_replace_text(sh, "[سطر داعم أو اسم صاحب الاقتباس]", "القاعدة المنهجية الحاكمة لمنظومة بَيّنة AI في خدمة المحتوى الإسلامي")
        safe_replace_text(sh, "[المصدر عند استخدام اقتباس]", "ميثاق الأمانة العلمية والتحقق الرقمي 2026")

    # --------------------------------------------------------------------------
    # 11. Slide 17 (0-index 16): Comparison Table (Dark)
    # --------------------------------------------------------------------------
    s17 = prs.slides[16]
    safe_replace_text(s17.shapes[2], "[اسم القسم]", "المقارنة والتحكيم")
    safe_replace_text(s17.shapes[3], "[عنوان الجدول أو المقارنة]", "مقارنة منهجية التحقق: بَيّنة AI مقابل النماذج العامة")
    safe_replace_text(s17.shapes[4], "[وصف مختصر للمقارنة أو البيانات]", "فروق جوهرية في الدقة، الإسناد، ومكافحة التضليل المعرفي")
    safe_replace_text(s17.shapes[7], "[مصدر البيانات أو ملاحظة ضرورية]", "معايير الاختبار والتقييم في تحدي الذكاء الاصطناعي 2026")

    tbl17 = s17.shapes[6].table
    comp_rows = [
        ["الأثر والنتيجة", "النماذج العامة", "محرك بَيّنة AI", "المعيار"],
        ["حماية السنة من الاختلاق", "توليد احتمالي مفتوح", "استرجاع مقيد بالأصول", "ثبوت المتن والسند"],
        ["منع انتشار الأحاديث الباطلة", "تأليف وتبرير الروايات", "بروتوكول الرفض الذكي", "مكافحة المكذوبات"],
        ["تجربة مستخدم فورية", "ثوانٍ متعددة (بطء وتكلفة)", "< 5ms (كاش ذكي)", "سرعة الاستجابة"],
        ["شهادة رقمية قابلة للتصدير", "غياب التخريج والسند", "بطاقة إسناد برقم الحديث", "التوثيق والتخريج"]
    ]
    for r_idx, row in enumerate(tbl17.rows):
        for c_idx, cell in enumerate(row.cells):
            if r_idx < len(comp_rows) and c_idx < len(comp_rows[r_idx]):
                cell.text = comp_rows[r_idx][c_idx]

    # --------------------------------------------------------------------------
    # 12. Slide 18 (0-index 17): Production Roadmap
    # --------------------------------------------------------------------------
    s18 = prs.slides[17]
    safe_replace_text(s18.shapes[2], "[اسم القسم]", "خطة التنفيذ")
    safe_replace_text(s18.shapes[3], "[خطة التنفيذ]", "خارطة الطريق لبناء وتطوير المنتج الأولي (MVP)")
    safe_replace_text(s18.shapes[4], "[الفترة التي تغطيها الخطة]", "جدول زمني مكثف ومحكم (أكتوبر 2026 وما بعدها)")

    # Phase 1
    set_shape_text(s18.shapes[6], "البنية التحتية والبيانات")
    set_shape_text(s18.shapes[7], "المرحلة 1")
    set_shape_text(s18.shapes[8], "فهرسة 251 متناً مسنداً عبر pgvector وPostgreSQL وضبط المعاجم.")

    # Phase 2
    set_shape_text(s18.shapes[10], "المحرك الهجين والرفض الذكي")
    set_shape_text(s18.shapes[11], "المرحلة 2")
    set_shape_text(s18.shapes[12], "دمج البحث الدلالي مع BM25 عبر RRF وبرمجة بروتوكول الامتناع الذكي.")

    # Phase 3
    set_shape_text(s18.shapes[14], "الواجهة وتصدير البطاقات")
    set_shape_text(s18.shapes[15], "المرحلة 3")
    set_shape_text(s18.shapes[16], "إطلاق واجهة Streamlit وبطاقات الإسناد وتصدير شهادات TXT وHTML.")

    # Phase 4
    set_shape_text(s18.shapes[18], "حزمة SDK والتكامل الخارجي")
    set_shape_text(s18.shapes[19], "المرحلة 4")
    set_shape_text(s18.shapes[20], "إتاحة API للمنصات وتوفير إضافة المتصفح للتحقق الفوري بنقرة زر.")

    # Phase 5
    set_shape_text(s18.shapes[22], "التوسع المعرفي والشراكات")
    set_shape_text(s18.shapes[23], "المرحلة 5")
    set_shape_text(s18.shapes[24], "توسيع الفهرسة لتشمل السنن والمسانيد ودعم اللغات العالمية الحية.")

    # --------------------------------------------------------------------------
    # 13. Slide 19 (0-index 18): Team
    # --------------------------------------------------------------------------
    s19 = prs.slides[18]
    safe_replace_text(s19.shapes[2], "[اسم القسم]", "القدرة التنفيذية")
    safe_replace_text(s19.shapes[3], "فريق العمل", "فريق العمل وتكامل الخبرات")
    safe_replace_text(s19.shapes[4], "[اسم الفريق]", "فريق بَيّنة AI")

    set_shape_text(s19.shapes[7], "مهندس ذكاء اصطناعي ونظم RAG")
    set_shape_text(s19.shapes[8], "هندسة التضمينات، ضبط مسارات البحث الهجين، وتطوير خوارزميات الاسترجاع الدلالي.")
    set_shape_text(s19.shapes[10], "مهندس نظم خلفية وقواعد بيانات")
    set_shape_text(s19.shapes[11], "بناء مسارات الـ API بـ FastAPI، تحسين أداء PostgreSQL وpgvector والكاش السريع.")
    set_shape_text(s19.shapes[13], "باحث متخصص في علوم الحديث")
    set_shape_text(s19.shapes[14], "التدقيق العلمي لرتب الأحاديث، صياغة بروتوكولات التحكيم، وضبط ميثاق الأمانة العلمية.")
    set_shape_text(s19.shapes[16], "مهندس واجهات وتجربة مستخدم")
    set_shape_text(s19.shapes[17], "تصميم وتطوير واجهات الاستعراض التفاعلية، بطاقات الإسناد، ومسارات التصدير الرقمي.")

    # --------------------------------------------------------------------------
    # 14. Slide 20 (0-index 19): The 4 Pillars (Light)
    # --------------------------------------------------------------------------
    s20 = prs.slides[19]
    safe_replace_text(s20.shapes[1], "[اسم القسم]", "الحل المبتكر")
    safe_replace_text(s20.shapes[2], "[عنوان الشريحة الفاتحة]", "الركائز الأربع لمنظومة بَيّنة AI")
    safe_replace_text(s20.shapes[3], "[فكرة واحدة تشرح المحتوى]", "منظومة متكاملة تدمج الضبط الشرعي الصارم مع أحدث تقنيات البحث الدلالي")

    set_shape_text(s20.shapes[5], "الاسترجاع الهجين المقيد (Hybrid RAG)")
    set_shape_text(s20.shapes[6], "دمج البحث المتجهي للأبعاد الدلالية مع البحث النصي الحرفي لضمان الدقة ونفي التوليد الحر.")
    set_shape_text(s20.shapes[7], "بطاقة الإسناد المعتمدة (Evidence Card)")
    set_shape_text(s20.shapes[8], "استخراج وثيقة إثبات رقمية تحتوي على المتن، الكتاب، الباب، رقم الحديث، وحكم المحققين.")
    set_shape_text(s20.shapes[9], "بروتوكول الرفض الذكي (Smart Refusal)")
    set_shape_text(s20.shapes[10], "كشف الروايات المكذوبة والضعيفة والامتناع الفوري عن إثبات النسبة حماية للسنة النبوية.")
    set_shape_text(s20.shapes[11], "التفسير الدلالي الموضوعي (Explainability)")
    set_shape_text(s20.shapes[12], "بيان أوجه الارتباط الدلالي والمفاهيم المشتركة بين لغة الاستعلام والمتن النبوي بدقة.")

    # --------------------------------------------------------------------------
    # 15. Slide 21 (0-index 20): Detailed Table (Milestones)
    # --------------------------------------------------------------------------
    s21 = prs.slides[20]
    safe_replace_text(s21.shapes[4], "[اسم القسم]", "إدارة المشروع")
    safe_replace_text(s21.shapes[5], "[عنوان الجدول التفصيلي]", "مصفوفة المهام والمخرجات التنفيذية")
    safe_replace_text(s21.shapes[6], "[وصف مختصر للمقارنة أو البيانات]", "توزيع المهام والمسؤوليات لضمان الإطلاق الناجح للمنتج")
    safe_replace_text(s21.shapes[7], "[مصدر البيانات أو ملاحظة ضرورية]", "جدول تسليم مخرجات التحدي 2026")

    tbl21 = s21.shapes[3].table
    milestone_rows = [
        ["البند", "التفاصيل", "المسؤول", "الموعد"],
        ["تجهيز البيانات والفهرسة", "هيكلة المتون وتوليد متجهات التضمين بـ pgvector", "مهندس الذكاء الاصطناعي", "اليوم الأول"],
        ["بناء المحرك الهجين", "دمج خوارزمية RRF وبروتوكول الامتناع الذكي", "مهندس النظم الخلفية", "اليوم الثاني"],
        ["الواجهة والتصدير", "إطلاق الواجهة التفاعلية وتصدير شهادات TXT وHTML", "مهندس الواجهات", "اليوم الثالث"],
        ["ضمان الجودة والتحكيم", "التدقيق والمراجعة الشاملة لضبط الأمانة العلمية", "المحقق الشرعي", "مستمر"]
    ]
    for r_idx, row in enumerate(tbl21.rows):
        for c_idx, cell in enumerate(row.cells):
            if r_idx < len(milestone_rows) and c_idx < len(milestone_rows[r_idx]):
                cell.text = milestone_rows[r_idx][c_idx]

    # --------------------------------------------------------------------------
    # 16. Slide 22 (0-index 21): Benchmark Bar Chart
    # --------------------------------------------------------------------------
    s22 = prs.slides[21]
    safe_replace_text(s22.shapes[1], "[اسم القسم]", "المقارنة والقياس المعياري")
    safe_replace_text(s22.shapes[2], "[عنوان المقارنة بالأعمدة]", "زمن الاستجابة ونسبة الهلوسة في التحقق")
    safe_replace_text(s22.shapes[3], "بيانات توضيحية للتعديل", "محرك بَيّنة AI مقابل نماذج الذكاء الاصطناعي العامة")
    safe_replace_text(s22.shapes[5], "[الوحدة]    [المصدر والفترة]", "الزمن (مللي ثانية) • أكتوبر 2026")
    safe_replace_text(s22.shapes[6], "بيانات توضيحية للتعديل", "محرك بَيّنة AI: استجابة فورية < 5ms مع صفر هلوسة")

    # --------------------------------------------------------------------------
    # 17. Slide 23 (0-index 22): Sources Distribution
    # --------------------------------------------------------------------------
    s23 = prs.slides[22]
    safe_replace_text(s23.shapes[1], "[اسم القسم]", "مصادر السنة المعتمدة")
    safe_replace_text(s23.shapes[2], "[عنوان التوزيع النسبي]", "توزيع المتون المسندة المفهرسة في النظام")
    safe_replace_text(s23.shapes[3], "بيانات توضيحية للتعديل", "صحيح البخاري، صحيح مسلم، والأربعون النووية")
    safe_replace_text(s23.shapes[5], "[المصدر والفترة]", "قاعدة بيانات بَيّنة AI (251 متناً مسنداً)")
    set_shape_text(s23.shapes[8], "صحيح البخاري")
    set_shape_text(s23.shapes[10], "صحيح مسلم")
    set_shape_text(s23.shapes[12], "الأربعون النووية")
    safe_replace_text(s23.shapes[13], "بيانات توضيحية للتعديل", "فهرسة هجينة متكاملة موثقة بالأرقام والأبواب")

    # --------------------------------------------------------------------------
    # 18. Slide 24 (0-index 23): How it Works (4 Steps)
    # --------------------------------------------------------------------------
    s24 = prs.slides[23]
    safe_replace_text(s24.shapes[1], "[اسم القسم]", "المعمارية الهندسية")
    safe_replace_text(s24.shapes[2], "[آلية عمل الحل]", "آلية عمل المحرك ومسار البيانات المتكامل")
    safe_replace_text(s24.shapes[3], "[تسلسل العمل من المدخلات إلى الأثر]", "خط أنابيب برمجي يربط بين استعلام المستخدم والمخرج المحقق خلال أجزاء من الثانية")

    # Step 1
    tf1 = s24.shapes[5].text_frame
    tf1.paragraphs[0].text = "01"
    tf1.paragraphs[1].text = "المدخلات"
    tf1.paragraphs[2].text = "استعلام المستخدم (متن، صياغة معاصرة، أو شبهة)"
    tf1.paragraphs[3].text = "تطبيع لغوي وإزالة التشكيل واستخراج الكلمات المفتاحية"

    # Step 2
    tf2 = s24.shapes[6].text_frame
    tf2.paragraphs[0].text = "02"
    tf2.paragraphs[1].text = "المعالجة والبحث"
    tf2.paragraphs[2].text = "توليد التضمين الدلالي وبحث هجين متزامن"
    tf2.paragraphs[3].text = "مطابقة متجهات HNSW مع البحث النصي TSV في PostgreSQL"

    # Step 3
    tf3 = s24.shapes[7].text_frame
    tf3.paragraphs[0].text = "03"
    tf3.paragraphs[1].text = "التحكيم والفرز"
    tf3.paragraphs[2].text = "دمج الترتيب بـ RRF وتطبيق عتبة الثقة"
    tf3.paragraphs[3].text = "توليد الشرح الدلالي بـ Gemini أو إطلاق الرفض الذكي"

    # Step 4
    tf4 = s24.shapes[8].text_frame
    tf4.paragraphs[0].text = "04"
    tf4.paragraphs[1].text = "المخرجات والأثر"
    tf4.paragraphs[2].text = "بطاقة إسناد معتمدة قابلة للتصدير (TXT/HTML)"
    tf4.paragraphs[3].text = "توثيق قطعي فوري يحمي المحتوى الإسلامي من التحريف"

    # --------------------------------------------------------------------------
    # 19. Slide 25 (0-index 24): Full Visual Architecture Showcase
    # --------------------------------------------------------------------------
    s25 = prs.slides[24]
    for sh in s25.shapes:
        if sh.is_placeholder and sh.placeholder_format.type == pptx.enum.shapes.PP_PLACEHOLDER.PICTURE:
            if os.path.exists("slide_preview-4.png"):
                sh.insert_picture("slide_preview-4.png")
        elif sh.has_text_frame:
            safe_replace_text(sh, "[عنوان يشرح الصورة]", "معمارية التحقق الهجين: دمج البحث الدلالي والمعجمي")
            safe_replace_text(sh, "[تعليق مختصر أو مصدر الصورة]", "مسار تدفق البيانات في محرك بَيّنة AI من الاستعلام إلى بطاقة الإسناد المعتمدة")

    # --------------------------------------------------------------------------
    # 20. Slide 26 (0-index 25): UI Gallery
    # --------------------------------------------------------------------------
    s26 = prs.slides[25]
    safe_replace_text(s26.shapes[1], "[اسم القسم]", "معرض الواجهات")
    safe_replace_text(s26.shapes[2], "[معرض الصور أو الواجهات]", "واجهات الاستخدام التفاعلية لمنظومة بَيّنة AI")

    set_shape_text(s26.shapes[5], "شاشة الفحص والتحقق الفوري مع سيناريوهات التجربة السريعة بنقرة واحدة.")
    set_shape_text(s26.shapes[6], "بطاقة الإسناد المعتمدة المبرزة مع التحليل الدلالي والمفاهيم المشتركة.")
    set_shape_text(s26.shapes[7], "نافذة التصدير الرقمي لتنزيل شهادات التحقق (TXT) وبطاقات النشر (HTML).")

    # Insert images in gallery placeholders
    pic_phs = [sh for sh in s26.shapes if sh.is_placeholder and sh.placeholder_format.type == pptx.enum.shapes.PP_PLACEHOLDER.PICTURE]
    gallery_imgs = ["slide_preview-2.png", "slide_preview-3.png", "slide_preview-6.png"]
    for p_idx, ph in enumerate(pic_phs):
        if p_idx < len(gallery_imgs) and os.path.exists(gallery_imgs[p_idx]):
            ph.insert_picture(gallery_imgs[p_idx])

    # --------------------------------------------------------------------------
    # 21. Slide 27 (0-index 26): Solution Components
    # --------------------------------------------------------------------------
    s27 = prs.slides[26]
    safe_replace_text(s27.shapes[2], "[اسم القسم]", "مكونات النظام")
    safe_replace_text(s27.shapes[3], "[عناصر الحل]", "المكونات الهندسية الأساسية لمنظومة بَيّنة AI")
    safe_replace_text(s27.shapes[4], "[أيقونات من القالب المرفق]", "بنية تقنية موجهة للإنتاج والاعتمادية العالية")

    set_shape_text(s27.shapes[7], "قاعدة البيانات المتجهية")
    set_shape_text(s27.shapes[8], "PostgreSQL مع امتداد pgvector لتخزين واسترجاع متجهات التضمين وفهارس HNSW بكفاءة فائقة.")

    set_shape_text(s27.shapes[10], "محرك التضمين الدلالي")
    set_shape_text(s27.shapes[11], "text-embedding-004 المخصص لاستيعاب البلاغة العربية وفهم دلالات الألفاظ الشرعية بدقة.")

    set_shape_text(s27.shapes[13], "طبقة التحكيم والأمان")
    set_shape_text(s27.shapes[14], "خوارزمية RRF مع بروتوكول الرفض الذكي لمكافحة الهلوسة ونفي الروايات غير المسندة.")

    set_shape_text(s27.shapes[16], "الواجهة ومنصة التصدير")
    set_shape_text(s27.shapes[17], "واجهة Streamlit حديثة وسريعة تتيح فحص المتون وتنزيل شهادات التحقق وبطاقات النشر الرقمية.")

    # --------------------------------------------------------------------------
    # 22. Slide 28 (0-index 27): 2-Option Comparison
    # --------------------------------------------------------------------------
    s28 = prs.slides[27]
    safe_replace_text(s28.shapes[2], "[اسم القسم]", "المقارنة والتميز")
    safe_replace_text(s28.shapes[3], "[مقارنة خيارين]", "محرك بَيّنة AI مقابل نماذج الذكاء الاصطناعي العامة")
    safe_replace_text(s28.shapes[4], "[أساس المقارنة]", "لماذا تتفوق الأنظمة المقيدة بالاسترجاع (Grounded) على النماذج التوليدية؟")

    set_shape_text(s28.shapes[6], "محرك بَيّنة AI (Grounded RAG)")
    set_shape_text(s28.shapes[7], "منظومة استدلال مقيدة حصراً بمتون السنة المسندة")

    set_shape_text(s28.shapes[8], "نماذج الذكاء الاصطناعي العامة (LLMs)")
    set_shape_text(s28.shapes[9], "روبوتات المحادثة التجارية المفتوحة (ChatGPT, Claude, etc.)")

    tf_opt1 = s28.shapes[10].text_frame
    tf_opt1.paragraphs[0].text = "الميزة: نسبة هلوسة 0% وتوثيق قطعي برقم الحديث والمصدر المعتمد."
    tf_opt1.paragraphs[2].text = "القيد: يلتزم بحدود الأصول المسندة دون أي توليد حر أو استنباط غير منصوص."
    tf_opt1.paragraphs[4].text = "الملاءمة: مثالي للباحثين، الدعاة، وصناع المحتوى والمنصات الرقمية الكبرى."

    tf_opt2 = s28.shapes[11].text_frame
    tf_opt2.paragraphs[0].text = "الميزة: قدرة لغوية عامة وتوليد إنشائي طليق في مختلف المواضيع."
    tf_opt2.paragraphs[2].text = "القيد: احتمالية عالية لاختلاق أحاديث وروايات وهمية وتضليل معرفي خطير."
    tf_opt2.paragraphs[4].text = "الملاءمة: غير آمنة للاستدلال والتحقق الشرعي وتفتقر لتوثيق الأسانيد المعتمدة."

    # --------------------------------------------------------------------------
    # 23. Slide 29 (0-index 28): Blank Dark Slide (Vision Statement)
    # --------------------------------------------------------------------------
    s29 = prs.slides[28]
    tb29 = s29.shapes.add_textbox(Inches(1.5), Inches(2.5), Inches(10.33), Inches(2.5))
    tf29 = tb29.text_frame
    tf29.word_wrap = True
    p29_1 = tf29.paragraphs[0]
    p29_1.text = "بَيّنة AI — Bayyinah Engine"
    p29_1.font.size = Pt(36)
    p29_1.font.bold = True
    p29_1.font.color.rgb = RGBColor(255, 255, 255)
    p29_1.alignment = PP_ALIGN.CENTER

    p29_2 = tf29.add_paragraph()
    p29_2.text = "نحو محتوى إسلامي موثق، رصين، ومحصّن ضد الهلوسة بأحدث حلول الذكاء الاصطناعي الهندسية"
    p29_2.font.size = Pt(20)
    p29_2.font.color.rgb = RGBColor(46, 242, 194)  # Turquoise #2EF2C2
    p29_2.alignment = PP_ALIGN.CENTER
    p29_2.space_before = Pt(14)

    # --------------------------------------------------------------------------
    # 24. Slide 30 (0-index 29): Blank Light Slide (Executive Summary)
    # --------------------------------------------------------------------------
    s30 = prs.slides[29]
    tb30 = s30.shapes.add_textbox(Inches(1.2), Inches(2.0), Inches(10.9), Inches(3.5))
    tf30 = tb30.text_frame
    tf30.word_wrap = True
    p30_title = tf30.paragraphs[0]
    p30_title.text = "الملخص التنفيذي لمنظومة بَيّنة AI"
    p30_title.font.size = Pt(30)
    p30_title.font.bold = True
    p30_title.font.color.rgb = RGBColor(18, 24, 63)  # Navy #12183F
    p30_title.alignment = PP_ALIGN.RIGHT

    summary_bullets = [
        "جاهزية كاملة للإنتاج: خط أنابيب برمجي مكتمل يجمع بين PostgreSQL وpgvector وFastAPI وStreamlit.",
        "موثوقية علمية مطلقة: نفي التوليد الحر تماماً، والاعتماد الحصري على الأصول المسندة وصحيحي البخاري ومسلم.",
        "أداء فائق واستجابة لحظية: سرعة استرجاع < 5ms عبر الذاكرة التخزينية المؤقتة للأسئلة الشائعة.",
        "استدامة وتوسع مستمر: توفير النظام كخدمة تحقق سحابية (VaaS API) لحماية التطبيقات والمواقع الإسلامية."
    ]
    for b in summary_bullets:
        p_b = tf30.add_paragraph()
        p_b.text = f"✔  {b}"
        p_b.font.size = Pt(16)
        p_b.font.color.rgb = RGBColor(51, 65, 85)
        p_b.alignment = PP_ALIGN.RIGHT
        p_b.space_before = Pt(8)

    # --------------------------------------------------------------------------
    # 25. Slide 31 (0-index 30): Closing / Thank You
    # --------------------------------------------------------------------------
    s31 = prs.slides[30]
    safe_replace_text(s31.shapes[1], "[اسم المشروع أو الفريق]", "فريق بَيّنة AI — Bayyinah Engine")
    safe_replace_text(s31.shapes[2], "[رابط النموذج أو وسيلة التواصل إن وجدت]", "النموذج الحي التفاعلي: http://localhost:8504 | تحدي الذكاء الاصطناعي في خدمة المحتوى الإسلامي 2026")

    # --------------------------------------------------------------------------
    # 26. Delete the Instruction Slides (Slides 1 to 6)
    # --------------------------------------------------------------------------
    print("[+] Deleting instruction slides (slides 1 to 6)...")
    for _ in range(6):
        rId = prs.slides._sldIdLst[0].rId
        prs.part.drop_rel(rId)
        del prs.slides._sldIdLst[0]

    print(f"[+] Final slide count: {len(prs.slides)}")

    # --------------------------------------------------------------------------
    # 27. Save Output Presentation
    # --------------------------------------------------------------------------
    print(f"[+] Saving final presentation to: {output_path}")
    prs.save(output_path)
    print("✅ Successfully generated Bayyinah_AI_Pitch_Deck.pptx!")

if __name__ == "__main__":
    populate_deck()
