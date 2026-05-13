import base64
from io import BytesIO
from PIL import Image


def load_and_resize(path: str, max_side: int = 1024) -> Image.Image:
    img = Image.open(path).convert("RGB")
    img.thumbnail((max_side, max_side), Image.LANCZOS)
    return img


def image_to_base64(img: Image.Image) -> str:
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


def prepare_for_gemini(path: str) -> dict:
    """Return a dict ready to pass as an inline_data part to Gemini."""
    img = load_and_resize(path)
    return {
        "inline_data": {
            "mime_type": "image/jpeg",
            "data": image_to_base64(img),
        }
    }


def pil_to_thumbnail(path: str, size: tuple = (300, 300)) -> Image.Image:
    img = Image.open(path).convert("RGB")
    img.thumbnail(size, Image.LANCZOS)
    return img