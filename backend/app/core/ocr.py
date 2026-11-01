import pytesseract
from PIL import Image


def recognize(image: Image.Image) -> tuple[str, bool]:
    data = pytesseract.image_to_data(image, lang="eng+hin", timeout=35, output_type=pytesseract.Output.DICT)
    words = [word for word in data["text"] if word.strip()]
    confidence = [float(c) for c, w in zip(data["conf"], data["text"]) if w.strip() and float(c) >= 0]
    return " ".join(words), not confidence or sum(confidence) / len(confidence) < 65
