#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بَيّنة AI — Bayyinah Engine
Polished 11-Slide Official Pitch Deck Generator
Targets: Bayyinah_AI_Final_Pitch_Deck_Fixed.pptx & Bayyinah_AI_Final_Pitch_Deck.pptx
Template: LcXbkXRzH232sfKL8cAgJ1AI7jQATxu2bP0S4EWu.pptx
"""

import os
import sys
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

# ==============================================================================
# Color Palette & Standards (Navy Dark Background #12183F)
# ==============================================================================
CYAN = RGBColor(46, 242, 194)        # #2EF2C2 - Accent headers, numbers, tags
WHITE = RGBColor(255, 255, 255)      # #FFFFFF - Main headings, primary values
LIGHT_BLUE = RGBColor(242, 244, 255) # #F2F4FF - Body text, descriptions, captions
MUTED_CYAN = RGBColor(160, 245, 225) # #A0F5E1 - Secondary accent

def format_run(run, font_size=None, bold=True, color=LIGHT_BLUE):
    """Applies font size, boldness, and high-contrast color to a text run."""
    if font_size is not None:
        run.font.size = font_size
    if bold is not None:
        run.font.bold = bold
    if color is not None:
        run.font.color.rgb = color

def safe_replace_text(shape, old_text, new_text, font_size=None, bold=True, color=None):
    """Replaces text in a shape while enforcing contrast and font sizing."""
    if not shape.has_text_frame:
        return False
    changed = False
    for p in shape.text_frame.paragraphs:
        if old_text in p.text:
            changed = True
            if len(p.runs) <= 1:
                p.text = p.text.replace(old_text, new_text)
                if len(p.runs) > 0:
                    format_run(p.runs[0], font_size, bold, color or LIGHT_BLUE)
            else:
                first_run = p.runs[0]
                full_text = p.text.replace(old_text, new_text)
                first_run.text = full_text
                format_run(first_run, font_size, bold, color or LIGHT_BLUE)
                for r in p.runs[1:]:
                    r.text = ""
    return changed

def set_shape_text(shape, text, font_size=Pt(18), bold=True, color=LIGHT_BLUE):
    """Sets shape text with explicit font size, boldness, and high-contrast color."""
    if not shape.has_text_frame:
        return
    tf = shape.text_frame
    p = tf.paragraphs[0]
    p.text = text
    if len(p.runs) > 0:
        format_run(p.runs[0], font_size, bold, color)
        for r in p.runs[1:]:
            r.text = ""
    # Clear any extra placeholder paragraphs
    for p_extra in tf.paragraphs[1:]:
        p_extra.text = ""

def set_para_text(p, text, font_size=Pt(18), bold=True, color=LIGHT_BLUE):
    """Sets paragraph text and styles its first run."""
    p.text = text
    if len(p.runs) > 0:
        format_run(p.runs[0], font_size, bold, color)
        for r in p.runs[1:]:
            r.text = ""

def format_table_cell(cell, text, font_size=Pt(16), bold=True, color=WHITE, align=PP_ALIGN.CENTER):
    """Formats table cell with explicit padding, alignment, font size, and color."""
    cell.text = text
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    for p in cell.text_frame.paragraphs:
        p.alignment = align
        for r in p.runs:
            format_run(r, font_size=font_size, bold=bold, color=color)

def remove_slide_numbers(slide):
    """Completely eliminates raw '‹#›' token from all shapes and tables on the slide."""
    for sh in slide.shapes:
        if sh.has_text_frame:
            for p in sh.text_frame.paragraphs:
                if "‹#›" in p.text:
                    p.text = p.text.replace("‹#›", "").strip()
        if sh.has_table:
            for row in sh.table.rows:
                for cell in row.cells:
                    if "‹#›" in cell.text:
                        cell.text = cell.text.replace("‹#›", "").strip()

def enforce_high_contrast(prs):
    """
    Global safety sweep:
    Ensures no paragraph run has None or dark color against the navy background,
    and enforces a minimum legible font size.
    """
    count_color_fixed = 0
    count_size_fixed = 0

    for slide_idx, slide in enumerate(prs.slides):
        for shape in slide.shapes:
            if shape.has_text_frame:
                for p in shape.text_frame.paragraphs:
                    for r in p.runs:
                        if not r.text.strip():
                            continue
                        
                        # Color check
                        c = r.font.color.rgb if r.font.color and r.font.color.type == pptx.enum.dml.MSO_COLOR_TYPE.RGB else None
                        if c is None:
                            r.font.color.rgb = LIGHT_BLUE
                            count_color_fixed += 1
                        else:
                            # Check luminance: R*0.299 + G*0.587 + B*0.114
                            lum = c[0] * 0.299 + c[1] * 0.587 + c[2] * 0.114
                            if lum < 120:  # dark color on navy background
                                r.font.color.rgb = LIGHT_BLUE
                                count_color_fixed += 1
                        
                        # Font size check (minimum 18pt for general text, 14pt allowed for tiny top badges)
                        current_sz = r.font.size.pt if r.font.size else 0
                        if current_sz < 14:
                            r.font.size = Pt(18)
                            count_size_fixed += 1
                        
                        # Ensure bold
                        if r.font.bold is None or r.font.bold is False:
                            r.font.bold = True

            if shape.has_table:
                for row in shape.table.rows:
                    for cell in row.cells:
                        for p in cell.text_frame.paragraphs:
                            for r in p.runs:
                                if not r.text.strip():
                                    continue
                                c = r.font.color.rgb if r.font.color and r.font.color.type == pptx.enum.dml.MSO_COLOR_TYPE.RGB else None
                                if c is None:
                                    r.font.color.rgb = WHITE
                                    count_color_fixed += 1
                                else:
                                    lum = c[0] * 0.299 + c[1] * 0.587 + c[2] * 0.114
                                    if lum < 120:
                                        r.font.color.rgb = WHITE
                                        count_color_fixed += 1
                                current_sz = r.font.size.pt if r.font.size else 0
                                if current_sz < 14:
                                    r.font.size = Pt(16)
                                    count_size_fixed += 1
                                r.font.bold = True

    print(f"[+] Global high-contrast sweep: fixed {count_color_fixed} colors, {count_size_fixed} font sizes.")

def generate_final_deck(
    template_path="LcXbkXRzH232sfKL8cAgJ1AI7jQATxu2bP0S4EWu.pptx",
    output_path="Bayyinah_AI_Final_Pitch_Deck_Fixed.pptx",
    sync_path="Bayyinah_AI_Final_Pitch_Deck.pptx"
):
    print(f"[+] Loading official PowerPoint template: {template_path}")
    prs = pptx.Presentation(template_path)
    print(f"[+] Initial slide count: {len(prs.slides)}")

    # Core 11 slides mapping (0-indexed in template):
    # 01. Cover: 7 (Slide 8)
    # 02. Problem: 10 (Slide 11)
    # 03. Solution: 26 (Slide 27)
    # 04. Architecture: 23 (Slide 24)
    # 05. Product UI: 12 (Slide 13)
    # 06. Smart Refusal: 13 (Slide 14)
    # 07. Metrics KPIs: 14 (Slide 15)
    # 08. Comparison Table: 16 (Slide 17)
    # 09. Team: 18 (Slide 19)
    # 10. Roadmap: 17 (Slide 18)
    # 11. Closing: 30 (Slide 31)
    target_indices = [7, 10, 26, 23, 12, 13, 14, 16, 18, 17, 30]

    # Filter slides to exactly these 11
    keep_elements = [prs.slides._sldIdLst[i] for i in target_indices]
    keep_rIds = set(el.rId for el in keep_elements)

    # Drop relationships for all excluded slides
    for el in list(prs.slides._sldIdLst):
        if el.rId not in keep_rIds:
            prs.part.drop_rel(el.rId)

    # Clear and repopulate _sldIdLst in target order
    sldIdLst = prs.slides._sldIdLst
    for el in list(sldIdLst):
        sldIdLst.remove(el)
    for el in keep_elements:
        sldIdLst.append(el)

    print(f"[+] Successfully reduced presentation to {len(prs.slides)} core slides.")

    # ==========================================================================
    # 1. Slide 1: Cover Slide (غلاف المشروع)
    # ==========================================================================
    s1 = prs.slides[0]
    safe_replace_text(s1.shapes[2], "[اسم المشروع]", "بَيّنة AI — Bayyinah Engine", font_size=Pt(44), bold=True, color=CYAN)
    safe_replace_text(s1.shapes[3], "[وصف الفكرة في سطرين]", 
        "محرك التحقق المعرفي وتتبع الأدلة الشرعية لتمكين المعرّفين بالإسلام وصنّاع المحتوى\n"
        "منظومة استدلال مقيدة بالاسترجاع (Grounded RAG) لمكافحة الهلوسة ونفي الروايات غير الثابتة",
        font_size=Pt(22), bold=True, color=LIGHT_BLUE
    )
    safe_replace_text(s1.shapes[5], "[اسم الفريق أو الجهة]", "فريق بَيّنة AI — تحدي الذكاء الاصطناعي في خدمة المحتوى الإسلامي 2026", font_size=Pt(18), bold=True, color=WHITE)
    safe_replace_text(s1.shapes[6], "[تاريخ العرض]", "ربيع الأول 1448هـ / أكتوبر 2026", font_size=Pt(18), bold=True, color=CYAN)

    # ==========================================================================
    # 2. Slide 2: Problem & Challenge (المشكلة وسياق التحدي)
    # ==========================================================================
    s2 = prs.slides[1]
    safe_replace_text(s2.shapes[1], "[اسم القسم]", "المشكلة وسياق التحدي", font_size=Pt(18), bold=True, color=CYAN)
    safe_replace_text(s2.shapes[2], "[عنوان الشريحة]", "معضلة الموثوقية في عصر الذكاء الاصطناعي", font_size=Pt(42), bold=True, color=WHITE)
    safe_replace_text(s2.shapes[3], "[فكرة واحدة تشرح ما سيقرأه الجمهور]", "تحديات واقعية تمس الأمانة العلمية وسلامة المحتوى الإسلامي الرقمي", font_size=Pt(22), bold=True, color=LIGHT_BLUE)

    set_shape_text(s2.shapes[5], "هلوسة النماذج التوليدية (LLMs)", font_size=Pt(24), bold=True, color=CYAN)
    set_shape_text(s2.shapes[6], "اختلاق أسانيد ومتون وهمية ونسبتها زوراً إلى النبي ﷺ لافتقار النماذج للتأصيل الحديثي.", font_size=Pt(18), bold=True, color=LIGHT_BLUE)

    set_shape_text(s2.shapes[7], "انتشار الروايات المكذوبة والضعيفة", font_size=Pt(24), bold=True, color=CYAN)
    set_shape_text(s2.shapes[8], "تداول مقولات لا أصل لها على شبكات التواصل بكثافة دون وجود أداة تحقق فورية وميسرة.", font_size=Pt(18), bold=True, color=LIGHT_BLUE)

    set_shape_text(s2.shapes[9], "مشقة التخريج والتحقق السريع", font_size=Pt(24), bold=True, color=CYAN)
    set_shape_text(s2.shapes[10], "صعوبة وصول الدعاة وصناع المحتوى للمصادر المسندة والتأكد من صحة المتن في ثوانٍ معدودة.", font_size=Pt(18), bold=True, color=LIGHT_BLUE)

    set_shape_text(s2.shapes[11], "غياب بطاقات الإسناد الرقمية", font_size=Pt(24), bold=True, color=CYAN)
    set_shape_text(s2.shapes[12], "افتقار المحتوى المنشور لوثائق إسناد رقمية معتمدة تدعم مصداقية الطرح أمام الجمهور العالمي.", font_size=Pt(18), bold=True, color=LIGHT_BLUE)

    # ==========================================================================
    # 3. Slide 3: Solution Pillars (الحل المبتكر وركائزه)
    # ==========================================================================
    s3 = prs.slides[2]
    safe_replace_text(s3.shapes[2], "[اسم القسم]", "الحل المبتكر", font_size=Pt(18), bold=True, color=CYAN)
    safe_replace_text(s3.shapes[3], "[عناصر الحل]", "الركائز الهندسية الأربع لمنظومة بَيّنة AI", font_size=Pt(42), bold=True, color=WHITE)
    safe_replace_text(s3.shapes[4], "[أيقونات من القالب المرفق]", "حل تقني متكامل يجمع بين الصرامة العلمية وأحدث تقنيات الذكاء الاصطناعي", font_size=Pt(22), bold=True, color=LIGHT_BLUE)

    set_shape_text(s3.shapes[7], "التقييد الصارم بالأصول (Grounded RAG)", font_size=Pt(24), bold=True, color=CYAN)
    set_shape_text(s3.shapes[8], "نفي التوليد الحر تماماً وحصر الاستدلال بمتون البخاري ومسلم والأربعين النووية.", font_size=Pt(18), bold=True, color=LIGHT_BLUE)

    set_shape_text(s3.shapes[10], "محرك البحث الدلالي والمعجمي الهجين", font_size=Pt(24), bold=True, color=CYAN)
    set_shape_text(s3.shapes[11], "دمج فهارس pgvector المتجهية مع البحث المعجمي بخوارزمية RRF لضمان أعلى دقة.", font_size=Pt(18), bold=True, color=LIGHT_BLUE)

    set_shape_text(s3.shapes[13], "بروتوكول الرفض الذكي (Smart Refusal)", font_size=Pt(24), bold=True, color=CYAN)
    set_shape_text(s3.shapes[14], "رصد فوري للأحاديث الباطلة والموضوعة ونفي نسبتها بحكم علمي معلل وصريح.", font_size=Pt(18), bold=True, color=LIGHT_BLUE)

    set_shape_text(s3.shapes[16], "بطاقة الإسناد والتصدير الرقمي", font_size=Pt(24), bold=True, color=CYAN)
    set_shape_text(s3.shapes[17], "توليد شهادة تحقق رقمية توثق المصدر والباب ورقم الحديث ونسبة التطابق الدلالي.", font_size=Pt(18), bold=True, color=LIGHT_BLUE)

    # ==========================================================================
    # 4. Slide 4: Architecture & Workflow (المعمارية الهندسية ومسار البيانات)
    # ==========================================================================
    s4 = prs.slides[3]
    safe_replace_text(s4.shapes[1], "[اسم القسم]", "المعمارية الهندسية", font_size=Pt(18), bold=True, color=CYAN)
    safe_replace_text(s4.shapes[2], "[آلية عمل الحل]", "آلية عمل المحرك ومسار البيانات المتكامل", font_size=Pt(42), bold=True, color=WHITE)
    safe_replace_text(s4.shapes[3], "[تسلسل العمل من المدخلات إلى الأثر]", "تدفق هندسي محكم من إدخال المتن وحتى إصدار بطاقة الإسناد الموثقة", font_size=Pt(22), bold=True, color=LIGHT_BLUE)

    # Step 1
    sh5_p = s4.shapes[5].text_frame.paragraphs
    set_para_text(sh5_p[0], "01", font_size=Pt(34), bold=True, color=CYAN)
    set_para_text(sh5_p[1], "الاستعلام الدلالي", font_size=Pt(24), bold=True, color=WHITE)
    set_para_text(sh5_p[2], "إدخال المتن أو الفكرة المراد فحصها وتحليلها دلالياً", font_size=Pt(18), bold=True, color=LIGHT_BLUE)
    set_para_text(sh5_p[3], "واجهة المستخدم أو استدعاء الـ API الخارجي", font_size=Pt(18), bold=True, color=CYAN)

    # Step 2
    sh6_p = s4.shapes[6].text_frame.paragraphs
    set_para_text(sh6_p[0], "02", font_size=Pt(34), bold=True, color=CYAN)
    set_para_text(sh6_p[1], "البحث الهجين RRF", font_size=Pt(24), bold=True, color=WHITE)
    set_para_text(sh6_p[2], "استرجاع متجهات text-embedding-004 ومطابقة الألفاظ", font_size=Pt(18), bold=True, color=LIGHT_BLUE)
    set_para_text(sh6_p[3], "قاعدة PostgreSQL مع امتداد pgvector وفهارس HNSW", font_size=Pt(18), bold=True, color=CYAN)

    # Step 3
    sh7_p = s4.shapes[7].text_frame.paragraphs
    set_para_text(sh7_p[0], "03", font_size=Pt(34), bold=True, color=CYAN)
    set_para_text(sh7_p[1], "التحكيم والرفض الذكي", font_size=Pt(24), bold=True, color=WHITE)
    set_para_text(sh7_p[2], "فحص عتبة القبول الصارمة (85%) ونفي الروايات غير الثابتة", font_size=Pt(18), bold=True, color=LIGHT_BLUE)
    set_para_text(sh7_p[3], "طبقة التحكيم المنطقي وبروتوكول منع الهلوسة", font_size=Pt(18), bold=True, color=CYAN)

    # Step 4
    sh8_p = s4.shapes[8].text_frame.paragraphs
    set_para_text(sh8_p[0], "04", font_size=Pt(34), bold=True, color=CYAN)
    set_para_text(sh8_p[1], "بطاقة الإسناد الموثقة", font_size=Pt(24), bold=True, color=WHITE)
    set_para_text(sh8_p[2], "إصدار النتيجة موثقة برقم الحديث والباب وتصدير الشهادة", font_size=Pt(18), bold=True, color=LIGHT_BLUE)
    set_para_text(sh8_p[3], "شهادة رقمية قابلة للمشاركة وزمن استجابة < 5ms", font_size=Pt(18), bold=True, color=CYAN)

    # ==========================================================================
    # 5. Slide 5: Product UI Screenshot (واجهة التطبيق التفاعلية الحقيقية)
    # ==========================================================================
    s5 = prs.slides[4]
    safe_replace_text(s5.shapes[1], "تحدي الذكاء الاصطناعي في خدمة المحتوى الإسلامي", "تحدي الذكاء الاصطناعي في خدمة المحتوى الإسلامي", font_size=Pt(14), bold=True, color=CYAN)
    safe_replace_text(s5.shapes[3], "[اسم القسم]", "واجهة التطبيق التفاعلية", font_size=Pt(18), bold=True, color=CYAN)
    safe_replace_text(s5.shapes[4], "[عنوان يشرح الصورة]", "تجربة تحقق فورية وموثقة عبر واجهة بَيّنة AI", font_size=Pt(38), bold=True, color=WHITE)
    
    # Right-hand Card 1
    safe_replace_text(s5.shapes[7], "[ما الذي نراه؟]", "بطاقة التحقق والإسناد المباشرة", font_size=Pt(24), bold=True, color=CYAN)
    safe_replace_text(s5.shapes[8], 
        "[اشرح ما تُظهره الصورة وكيف يدعم ذلك فكرة المشروع.]",
        "فحص فوري لحديث «إنما الأعمال بالنيات» بنسبة تطابق 96.4%، مع استخراج الكتاب والباب وتخريج الحديث في صحيح البخاري، وإبراز المفاهيم الدلالية المطابقة.",
        font_size=Pt(18), bold=True, color=LIGHT_BLUE
    )

    # Right-hand Card 2
    safe_replace_text(s5.shapes[9], "[ما الذي يهم المستخدم؟]", "التوثيق والتصدير الفوري", font_size=Pt(24), bold=True, color=CYAN)
    safe_replace_text(s5.shapes[10],
        "[اذكر الفائدة أو النتيجة التي يوضحها هذا المثال.]",
        "إمكانية تصدير بطاقة إسناد وشهادة تحقق رقمية جاهزة للنشر، مع زمن استجابة لحظي يعزز موثوقية المحتوى الدعوي والمعرفي.",
        font_size=Pt(18), bold=True, color=LIGHT_BLUE
    )

    # Insert Real Screenshot into Native Picture Placeholder (Shape 6)
    if os.path.exists("streamlit_ui_verified.png"):
        print("[+] Inserting real verified UI screenshot into Slide 5...")
        s5.shapes[6].insert_picture("streamlit_ui_verified.png")
    else:
        print("[!] Warning: streamlit_ui_verified.png not found!")

    # ==========================================================================
    # 6. Slide 6: Smart Refusal Screenshot (بروتوكول الرفض الذكي الحقيقي)
    # ==========================================================================
    s6 = prs.slides[5]
    safe_replace_text(s6.shapes[1], "تحدي الذكاء الاصطناعي في خدمة المحتوى الإسلامي", "تحدي الذكاء الاصطناعي في خدمة المحتوى الإسلامي", font_size=Pt(14), bold=True, color=CYAN)
    safe_replace_text(s6.shapes[3], "[اسم القسم]", "بروتوكول الرفض الذكي", font_size=Pt(18), bold=True, color=CYAN)
    safe_replace_text(s6.shapes[4], "[عنوان يشرح الصورة المربعة]", "كشف الروايات المكذوبة والامتناع الصارم عن التوليد", font_size=Pt(38), bold=True, color=WHITE)
    
    # Left-hand Card
    safe_replace_text(s6.shapes[7], "[الفكرة الرئيسية]", "تحصين المحتوى ضد الأحاديث الموضوعة والباطلة", font_size=Pt(26), bold=True, color=CYAN)
    safe_replace_text(s6.shapes[8],
        "[نص موجز يوضح ما في الصورة، ولماذا أضفتها إلى العرض. ركّز على رسالة واحدة يمكن فهمها سريعًا.]",
        "عند فحص مقولة مشهورة مكذوبة («اطلبوا العلم ولو في الصين»)، يكتشف المحرك عدم ثبوتها في صحيحي البخاري ومسلم، ويهبط مؤشر التطابق إلى ما دون عتبة القبول، فيصدر النظام تنبيهاً صريحاً يمتنع فيه عن الإسناد أو التوليد.",
        font_size=Pt(18), bold=True, color=LIGHT_BLUE
    )
    # Bottom Caption
    safe_replace_text(s6.shapes[9], "[تعليق أو مصدر الصورة]", 
        "بروتوكول الرفض الذكي لمنظومة بَيّنة AI — تصفير تام للهلوثة وحماية للأمانة العلمية",
        font_size=Pt(18), bold=True, color=WHITE
    )

    # Insert Real Refusal Screenshot into Native Picture Placeholder (Shape 6)
    if os.path.exists("streamlit_ui_refused.png"):
        print("[+] Inserting real refusal UI screenshot into Slide 6...")
        s6.shapes[6].insert_picture("streamlit_ui_refused.png")
    else:
        print("[!] Warning: streamlit_ui_refused.png not found!")

    # ==========================================================================
    # 7. Slide 7: Metrics KPIs (الأثر والمؤشرات الكمية)
    # ==========================================================================
    s7 = prs.slides[6]
    safe_replace_text(s7.shapes[1], "تحدي الذكاء الاصطناعي في خدمة المحتوى الإسلامي", "تحدي الذكاء الاصطناعي في خدمة المحتوى الإسلامي", font_size=Pt(14), bold=True, color=CYAN)
    safe_replace_text(s7.shapes[3], "[اسم القسم]", "الأثر والمؤشرات", font_size=Pt(18), bold=True, color=CYAN)
    safe_replace_text(s7.shapes[4], "[الأثر أو المؤشرات]", "مؤشرات الكفاءة الهندسية والأمانة العلمية", font_size=Pt(40), bold=True, color=WHITE)
    safe_replace_text(s7.shapes[5], "[الفترة أو عينة القياس]", "بيئة الإنتاج والقياس المعياري الفعلي 2026", font_size=Pt(20), bold=True, color=LIGHT_BLUE)

    # KPI 1
    set_shape_text(s7.shapes[7], "0%", font_size=Pt(64), bold=True, color=CYAN)
    set_shape_text(s7.shapes[8], "نسبة الهلوسة الرقمية", font_size=Pt(24), bold=True, color=WHITE)
    set_shape_text(s7.shapes[9], "تصفير تام للتوليد الحر", font_size=Pt(18), bold=True, color=LIGHT_BLUE)

    # KPI 2
    set_shape_text(s7.shapes[10], "< 5ms", font_size=Pt(64), bold=True, color=CYAN)
    set_shape_text(s7.shapes[11], "زمن استجابة الكاش", font_size=Pt(24), bold=True, color=WHITE)
    set_shape_text(s7.shapes[12], "استرجاع فوري للذاكرة المؤقتة", font_size=Pt(18), bold=True, color=LIGHT_BLUE)

    # KPI 3
    set_shape_text(s7.shapes[13], "+95%", font_size=Pt(64), bold=True, color=CYAN)
    set_shape_text(s7.shapes[14], "دقة المطابقة الدلالية", font_size=Pt(24), bold=True, color=WHITE)
    set_shape_text(s7.shapes[15], "تطابق دلالي ولفظي هجين", font_size=Pt(18), bold=True, color=LIGHT_BLUE)

    # KPI 4
    set_shape_text(s7.shapes[16], "100%", font_size=Pt(64), bold=True, color=CYAN)
    set_shape_text(s7.shapes[17], "شفافية الإسناد والعزو", font_size=Pt(24), bold=True, color=WHITE)
    set_shape_text(s7.shapes[18], "توثيق قطعي بالأبواب والأرقام", font_size=Pt(18), bold=True, color=LIGHT_BLUE)

    safe_replace_text(s7.shapes[19], "[مصدر البيانات وتاريخها]", "سجلات القياس المعياري لنظام بَيّنة AI — أكتوبر 2026", font_size=Pt(18), bold=True, color=LIGHT_BLUE)

    # ==========================================================================
    # 8. Slide 8: Comparison Table (جدول المقارنة المعيارية)
    # ==========================================================================
    s8 = prs.slides[7]
    safe_replace_text(s8.shapes[2], "[اسم القسم]", "المقارنة والتحكيم", font_size=Pt(18), bold=True, color=CYAN)
    safe_replace_text(s8.shapes[3], "[عنوان الجدول أو المقارنة]", "مقارنة منهجية التحقق: بَيّنة AI مقابل النماذج العامة", font_size=Pt(40), bold=True, color=WHITE)
    safe_replace_text(s8.shapes[4], "[وصف مختصر للمقارنة أو البيانات]", "لماذا تتفوق الأنظمة المقيدة بالاسترجاع (Grounded RAG) على روبوتات المحادثة العامة؟", font_size=Pt(20), bold=True, color=LIGHT_BLUE)

    tbl_shape = None
    for sh in s8.shapes:
        if sh.has_table:
            tbl_shape = sh
            break

    if tbl_shape:
        table = tbl_shape.table
        # Headers: Table indices (RTL in PPTX: Col 3 is rightmost, Col 0 is leftmost)
        format_table_cell(table.cell(0, 3), "معيار المقارنة", font_size=Pt(18), bold=True, color=CYAN)
        format_table_cell(table.cell(0, 2), "نماذج الذكاء الاصطناعي العامة (LLMs)", font_size=Pt(18), bold=True, color=CYAN)
        format_table_cell(table.cell(0, 1), "محرك بَيّنة AI (Grounded RAG)", font_size=Pt(18), bold=True, color=CYAN)
        format_table_cell(table.cell(0, 0), "الأثر والتميز", font_size=Pt(18), bold=True, color=CYAN)

        # Row 1
        format_table_cell(table.cell(1, 3), "الاعتماد على المصادر", font_size=Pt(16), bold=True, color=WHITE)
        format_table_cell(table.cell(1, 2), "توليد احتمالي عام من بيانات الويب غير المنقحة", font_size=Pt(16), bold=True, color=LIGHT_BLUE)
        format_table_cell(table.cell(1, 1), "تقييد قطعي بالأصول المسندة (البخاري ومسلم)", font_size=Pt(16), bold=True, color=WHITE)
        format_table_cell(table.cell(1, 0), "موثوقية علمية مطلقة", font_size=Pt(16), bold=True, color=CYAN)

        # Row 2
        format_table_cell(table.cell(2, 3), "نسبة الهلوسة واختلاق الأحاديث", font_size=Pt(16), bold=True, color=WHITE)
        format_table_cell(table.cell(2, 2), "مرتفعة (تختلق أسانيد ومتون وهمية وتنسبها)", font_size=Pt(16), bold=True, color=LIGHT_BLUE)
        format_table_cell(table.cell(2, 1), "صفرية (0% - بروتوكول رفض صارم)", font_size=Pt(16), bold=True, color=WHITE)
        format_table_cell(table.cell(2, 0), "أمان شرعي ومعرفي", font_size=Pt(16), bold=True, color=CYAN)

        # Row 3
        format_table_cell(table.cell(3, 3), "سرعة الاستجابة والتكلفة", font_size=Pt(16), bold=True, color=WHITE)
        format_table_cell(table.cell(3, 2), "استجابة بطيئة (1.5 - 3 ثوانٍ) وتكلفة متكررة", font_size=Pt(16), bold=True, color=LIGHT_BLUE)
        format_table_cell(table.cell(3, 1), "فورية (< 5ms بالكاش) وتكلفة تشغيل منخفضة", font_size=Pt(16), bold=True, color=WHITE)
        format_table_cell(table.cell(3, 0), "كفاءة تشغيلية فائقة", font_size=Pt(16), bold=True, color=CYAN)

        # Row 4
        format_table_cell(table.cell(4, 3), "شفافية العزو والتوثيق", font_size=Pt(16), bold=True, color=WHITE)
        format_table_cell(table.cell(4, 2), "إجابات نصية إنشائية دون عزو منضبط", font_size=Pt(16), bold=True, color=LIGHT_BLUE)
        format_table_cell(table.cell(4, 1), "بطاقة إسناد رقمية معتمدة برقم الحديث والباب", font_size=Pt(16), bold=True, color=WHITE)
        format_table_cell(table.cell(4, 0), "جاهزية تامة للنشر", font_size=Pt(16), bold=True, color=CYAN)

    safe_replace_text(s8.shapes[7], "[مصدر البيانات أو ملاحظة ضرورية]", "القياس المعياري لبيئة الإنتاج — تحدي الذكاء الاصطناعي في خدمة المحتوى الإسلامي 2026", font_size=Pt(18), bold=True, color=LIGHT_BLUE)

    # ==========================================================================
    # 9. Slide 9: Team (القدرة التنفيذية وفريق العمل)
    # ==========================================================================
    s9 = prs.slides[8]
    safe_replace_text(s9.shapes[2], "[اسم القسم]", "القدرة التنفيذية", font_size=Pt(18), bold=True, color=CYAN)
    safe_replace_text(s9.shapes[3], "فريق العمل", "فريق العمل والتنفيذ", font_size=Pt(42), bold=True, color=WHITE)
    safe_replace_text(s9.shapes[4], "[اسم الفريق]", "فريق بَيّنة AI — تكامل هندسي ومعرفي متكامل", font_size=Pt(22), bold=True, color=LIGHT_BLUE)

    # Member 1
    set_shape_text(s9.shapes[7], "مهندس الذكاء الاصطناعي وأنظمة RAG", font_size=Pt(24), bold=True, color=CYAN)
    set_shape_text(s9.shapes[8], "تطوير معمارية البحث الهجين، فهارس pgvector، وضبط نماذج التضمين الدلالي text-embedding-004.", font_size=Pt(18), bold=True, color=WHITE)

    # Member 2
    set_shape_text(s9.shapes[10], "مهندس البرمجيات والبنية التحتية", font_size=Pt(24), bold=True, color=CYAN)
    set_shape_text(s9.shapes[11], "بناء خط أنابيب البيانات، خدمات FastAPI، كاش الذاكرة المؤقتة، ونشر الحاويات عبر Docker.", font_size=Pt(18), bold=True, color=WHITE)

    # Member 3
    set_shape_text(s9.shapes[13], "مستشار المحتوى الرقمي والتحقيق الشرعي", font_size=Pt(24), bold=True, color=CYAN)
    set_shape_text(s9.shapes[14], "تدقيق معايير الأمانة العلمية، مطابقة أصول الروايات، وبناء سيناريوهات الرفض الذكي.", font_size=Pt(18), bold=True, color=WHITE)

    # Member 4
    set_shape_text(s9.shapes[16], "مهندس تجربة المستخدم والمنتج الرقمي", font_size=Pt(24), bold=True, color=CYAN)
    set_shape_text(s9.shapes[17], "تصميم واجهة Streamlit المتجاوبة، بطاقات الإسناد القابلة للتصدير، وتكامل منصات النشر.", font_size=Pt(18), bold=True, color=WHITE)

    # ==========================================================================
    # 10. Slide 10: Roadmap (خطة التنفيذ وخارطة الطريق)
    # ==========================================================================
    s10 = prs.slides[9]
    safe_replace_text(s10.shapes[2], "[اسم القسم]", "خطة التنفيذ", font_size=Pt(18), bold=True, color=CYAN)
    safe_replace_text(s10.shapes[3], "[خطة التنفيذ]", "خارطة طريق التطوير من النموذج الأولي إلى الإطلاق الشامل", font_size=Pt(40), bold=True, color=WHITE)
    safe_replace_text(s10.shapes[4], "[الفترة التي تغطيها الخطة]", "الجدول الزمني 2026 - 2027", font_size=Pt(22), bold=True, color=LIGHT_BLUE)

    # Phase 1
    set_shape_text(s10.shapes[5], "01", font_size=Pt(34), bold=True, color=CYAN)
    set_shape_text(s10.shapes[6], "تأسيس قاعدة المعرفة", font_size=Pt(24), bold=True, color=WHITE)
    set_shape_text(s10.shapes[7], "المرحلة 1: الربع الأول 2026", font_size=Pt(18), bold=True, color=CYAN)
    set_shape_text(s10.shapes[8], "جمع وتدقيق متون صحيحي البخاري ومسلم والأربعين النووية وتوليد متجهات pgvector.", font_size=Pt(18), bold=True, color=LIGHT_BLUE)

    # Phase 2
    set_shape_text(s10.shapes[9], "02", font_size=Pt(34), bold=True, color=CYAN)
    set_shape_text(s10.shapes[10], "تطوير محرك البحث والكاش", font_size=Pt(24), bold=True, color=WHITE)
    set_shape_text(s10.shapes[11], "المرحلة 2: الربع الثاني 2026", font_size=Pt(18), bold=True, color=CYAN)
    set_shape_text(s10.shapes[12], "دمج خوارزمية RRF الهجينة وتفعيل ذاكرة الكاش اللحظية واستقرار خدمات FastAPI.", font_size=Pt(18), bold=True, color=LIGHT_BLUE)

    # Phase 3
    set_shape_text(s10.shapes[13], "03", font_size=Pt(34), bold=True, color=CYAN)
    set_shape_text(s10.shapes[14], "بناء الواجهة وبطاقات الإسناد", font_size=Pt(24), bold=True, color=WHITE)
    set_shape_text(s10.shapes[15], "المرحلة 3: الربع الثالث 2026", font_size=Pt(18), bold=True, color=CYAN)
    set_shape_text(s10.shapes[16], "إطلاق واجهة المستخدم التفاعلية وتضمين ميزة تصدير بطاقات الإسناد وشهادات التحقق.", font_size=Pt(18), bold=True, color=LIGHT_BLUE)

    # Phase 4
    set_shape_text(s10.shapes[17], "04", font_size=Pt(34), bold=True, color=CYAN)
    set_shape_text(s10.shapes[18], "التحكيم والقياس المعياري", font_size=Pt(24), bold=True, color=WHITE)
    set_shape_text(s10.shapes[19], "المرحلة 4: أكتوبر 2026", font_size=Pt(18), bold=True, color=CYAN)
    set_shape_text(s10.shapes[20], "المشاركة في هاكاثون المحتوى الإسلامي، اختبار صفر هلوسة، وإثبات تفوق الأداء.", font_size=Pt(18), bold=True, color=LIGHT_BLUE)

    # Phase 5
    set_shape_text(s10.shapes[21], "05", font_size=Pt(34), bold=True, color=CYAN)
    set_shape_text(s10.shapes[22], "التوسع السحابي (VaaS API)", font_size=Pt(24), bold=True, color=WHITE)
    set_shape_text(s10.shapes[23], "المرحلة 5: 2027", font_size=Pt(18), bold=True, color=CYAN)
    set_shape_text(s10.shapes[24], "إتاحة محرك التحقق كخدمة سحابية لكافة التطبيقات والمنصات الإسلامية وصناع المحتوى.", font_size=Pt(18), bold=True, color=LIGHT_BLUE)

    # ==========================================================================
    # 11. Slide 11: Closing Slide (الختام والتواصل والملخص)
    # ==========================================================================
    s11 = prs.slides[10]
    safe_replace_text(s11.shapes[1], "[اسم المشروع أو الفريق]", "فريق بَيّنة AI — Bayyinah Engine", font_size=Pt(28), bold=True, color=WHITE)
    safe_replace_text(s11.shapes[2], "[رابط النموذج أو وسيلة التواصل إن وجدت]", 
        "النموذج الحي التفاعلي: http://localhost:8504 | تحدي الذكاء الاصطناعي في خدمة المحتوى الإسلامي 2026",
        font_size=Pt(20), bold=True, color=CYAN
    )

    # ==========================================================================
    # Global Cleanups: Remove all raw '‹#›' tokens and residual brackets
    # ==========================================================================
    print("[+] Cleaning raw slide number tokens '‹#›' across all 11 slides...")
    for idx, slide in enumerate(prs.slides):
        remove_slide_numbers(slide)

    # ==========================================================================
    # Enforce High-Contrast and Font Sizing Across All Slides
    # ==========================================================================
    print("[+] Running global high-contrast and readability enforcement sweep...")
    enforce_high_contrast(prs)

    # Save final polished presentation to both target names
    print(f"[+] Saving polished pitch deck to: {output_path}")
    prs.save(output_path)
    if sync_path and sync_path != output_path:
        print(f"[+] Syncing to: {sync_path}")
        prs.save(sync_path)
    print("✅ Successfully generated polished high-contrast pitch decks!")

if __name__ == "__main__":
    generate_final_deck()
