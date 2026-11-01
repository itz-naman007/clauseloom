import io
import os
import re
from threading import Lock
from html import escape
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT_LOCK = Lock()


def make_report(result: dict) -> bytes:
    """Generate an in-memory report with embedded Unicode fonts when available."""
    regular = os.getenv("REPORT_FONT", "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf")
    hindi = os.getenv("REPORT_HINDI_FONT", "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf")
    if not Path(regular).exists() and Path("C:/Windows/Fonts/Nirmala.ttc").exists():
        regular = "C:/Windows/Fonts/Nirmala.ttc"
    if not Path(hindi).exists():
        hindi = regular
    family = "Helvetica"
    hindi_family = None
    with FONT_LOCK:
        if Path(regular).exists():
            if "ClauseLoom" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("ClauseLoom", regular))
            family = "ClauseLoom"
        if Path(hindi).exists():
            if "ClauseLoomHindi" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("ClauseLoomHindi", hindi))
            hindi_family = "ClauseLoomHindi"
    styles = getSampleStyleSheet()
    for name in ["Normal", "Title", "Heading1", "Heading2", "Heading3"]:
        styles[name].fontName = family
        styles[name].shaping = True
    styles.add(ParagraphStyle("Body", fontName=family, fontSize=9, leading=14, spaceAfter=8, alignment=TA_LEFT, shaping=True))
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, title="ClauseLoom contract report", author="ClauseLoom", topMargin=40, bottomMargin=40)
    story = []

    def p(value, style="Body"):
        content = escape(str(value)).replace("\n", "<br/>")
        if hindi_family:
            content = re.sub(r"[\u0900-\u097f]+", lambda match: f'<font name="{hindi_family}">{match[0]}</font>', content)
        return Paragraph(content, styles[style])

    story += [
        p("ClauseLoom | Unravel the fine print.", "Title"),
        p("This tool provides plain-language information, not legal advice. For important decisions consult a qualified lawyer."),
    ]
    summary = result["summary"]
    story += [
        p(f"Review score: {summary['overall_score']} / 100", "Heading1"),
        p(summary["label"]),
        p(summary["formula"]),
        p("The score counts detected flags. A low score does not establish safety."),
    ]
    for warning in result["doc_info"]["warnings"]:
        story.append(p(warning))
    story.append(p("Key terms", "Heading2"))
    for key, value in result["key_terms"].items():
        story.append(p(f"{key.replace('_', ' ').title()}: {value or 'Not found'}"))
    for item in result["clauses"]:
        clause = item["clause"]
        story += [
            Spacer(1, 10),
            p(f"Clause {clause['index']} · Page {clause['page']} · {item['explanation']['risk_level'].upper()}", "Heading2"),
            p(clause["text"]),
            p(item["explanation"]["plain_summary"]),
            p("Confidence: " + item["confidence"]),
        ]
        for flag in item["flags"]:
            story.append(
                KeepTogether(
                    [
                        p(f"{flag['severity'].upper()} · {flag['category']}", "Heading3"),
                        p("Evidence: " + (flag["matched_text"] or "Document-wide absence check; no quote.")),
                        p(flag["explanation_template"]),
                        p("Ask: " + flag["suggestion_template"]),
                    ]
                )
            )

    def footer(canvas, doc):
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#52645d"))
        canvas.drawString(40, 22, "ClauseLoom | Informational only | Downloaded copies are yours to manage")
        canvas.drawRightString(555, 22, str(doc.page))

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()
