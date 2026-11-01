"""Generate bundled fictional PDFs and DOCX files for parser demos."""
from pathlib import Path
from html import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from docx import Document

ROOT=Path(__file__).resolve().parents[1]
styles=getSampleStyleSheet()
for kind in ['rental','freelance']:
    text=(ROOT/f'samples/sample_{kind}.txt').read_text(encoding='utf-8').replace('—','-')
    paragraphs=text.split('\n\n')
    story=[]
    doc=Document()
    for i,paragraph in enumerate(paragraphs):
        heading,*body=paragraph.split('\n',1)
        story.append(Paragraph(escape(heading),styles['Heading1' if i==0 else 'Heading2']))
        doc.add_heading(heading,level=1 if i==0 else 2)
        if body:
            story.append(Paragraph(escape(body[0]),styles['BodyText']))
            doc.add_paragraph(body[0])
        story.append(Spacer(1,10))
    SimpleDocTemplate(str(ROOT/f'samples/sample_{kind}.pdf')).build(story)
    doc.save(ROOT/f'samples/sample_{kind}.docx')
