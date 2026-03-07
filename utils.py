import base64
import re


def sanitize_filename(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_-]", "_", value)
    return value[:100] or "generated_image"


def normalize_b64(data: str) -> str:
    if data.startswith("data:") and "," in data:
        return data.split(",", 1)[1]
    return data


def decode_b64_image(b64_data: str) -> bytes:
    try:
        return base64.b64decode(normalize_b64(b64_data), validate=True)
    except Exception as e:
        raise ValueError("Une image fournie n'est pas un base64 valide") from e


def image_file_to_b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")