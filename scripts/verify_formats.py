"""Verify the deployed upload pipeline with fictional PDF, DOCX and OCR inputs."""

import argparse
import io
import json
from pathlib import Path

import httpx
from docx import Document
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas

parser = argparse.ArgumentParser()
parser.add_argument("--base", default="http://127.0.0.1:7860")
args = parser.parse_args()
text = "1. Payment\nThe client pays the freelancer INR 1000 within 90 days."
files = []
buffer = io.BytesIO()
pdf = canvas.Canvas(buffer)
pdf.drawString(40, 750, "1. Payment")
pdf.drawString(40, 725, text.splitlines()[1])
pdf.save()
files.append(("contract.pdf", buffer.getvalue()))
buffer = io.BytesIO()
doc = Document()
for line in text.splitlines():
    doc.add_paragraph(line)
doc.save(buffer)
files.append(("contract.docx", buffer.getvalue()))
font_paths = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "C:/Windows/Fonts/arial.ttf"]
font = ImageFont.truetype(next(path for path in font_paths if Path(path).exists()), 25)
image = Image.new("RGB", (1100, 180), "white")
ImageDraw.Draw(image).multiline_text((25, 25), text, fill="black", font=font, spacing=15)
for extension, encoding in [("png", "PNG"), ("jpg", "JPEG")]:
    buffer = io.BytesIO()
    image.save(buffer, format=encoding)
    files.append((f"contract.{extension}", buffer.getvalue()))

with httpx.Client(base_url=args.base, timeout=600, trust_env=False) as client:
    client.get("/api/ready").raise_for_status()
    rejected = client.post(
        "/api/analyze", headers={"Origin": "https://untrusted.example"}, files={"file": files[0]}
    )
    assert rejected.status_code == 403, "Cross-site upload was accepted"
    for filename, data in files:
        response = client.post("/api/analyze", files={"file": (filename, data)}, data={"doc_type": "freelance"})
        response.raise_for_status()
        sid = response.json()["session_id"]
        try:
            with client.stream("GET", f"/api/analyze/{sid}/stream") as stream:
                stream.raise_for_status()
                events = [line for line in stream.iter_lines() if line.startswith("event:")]
            assert "event: done" in events and "event: error" not in events, (filename, events)
            result = client.get(f"/api/analyze/{sid}")
            result.raise_for_status()
            body = result.json()
            source = " ".join(item["clause"]["text"] for item in body["clauses"])
            assert "90" in source and "1000" in source, (filename, source)
            assert any(item["flags"] for item in body["clauses"]), filename
            if filename.endswith((".png", ".jpg")):
                assert any("OCR used" in warning for warning in body["doc_info"]["warnings"])
            print(json.dumps({"format": filename, "extraction": "passed", "stream": "passed"}), flush=True)
        finally:
            assert client.delete(f"/api/analyze/{sid}").status_code == 200
            assert client.get(f"/api/analyze/{sid}").status_code == 404
    print("PASS: PDF, DOCX, PNG/JPEG OCR, origin rejection and deletion", flush=True)
