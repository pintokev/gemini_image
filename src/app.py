import base64
import hmac
import os
from threading import Lock

from flask import Flask, jsonify, request
from google import genai

from src.gemini_image import generate_image
from src.config import settings


app = Flask(__name__)

gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)

ALLOWED_MIME_TYPES = {"image/png", "image/jpeg", "image/webp"}

# Historique simple en mémoire : {thread_id: {"b64_data": "...", "mime_type": "..."}}
LAST_IMAGE_BY_THREAD_ID = {}
LAST_IMAGE_LOCK = Lock()


@app.before_request
def require_internal_api_token():
    expected_token = settings.INTERNAL_API_TOKEN
    if not expected_token or request.path == "/health":
        return None

    provided_token = request.headers.get("X-Internal-Api-Token", "")
    if not hmac.compare_digest(provided_token, expected_token):
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    return None


def extract_images_from_request():
    input_images_b64 = []
    input_mime_type = None

    files = request.files.getlist("files")
    if not files:
        return input_images_b64, input_mime_type

    for file in files:
        mime_type = (file.content_type or "").lower()

        if mime_type not in ALLOWED_MIME_TYPES:
            continue

        file_bytes = file.read()
        if not file_bytes:
            continue

        input_images_b64.append(base64.b64encode(file_bytes).decode("utf-8"))

        if input_mime_type is None:
            input_mime_type = mime_type

    return input_images_b64, input_mime_type


def get_last_image_for_thread(thread_id: str):
    if not thread_id:
        return None

    with LAST_IMAGE_LOCK:
        return LAST_IMAGE_BY_THREAD_ID.get(thread_id)


def set_last_image_for_thread(thread_id: str, image: dict):
    if not thread_id:
        return

    b64_data = base64.b64encode(image["data"]).decode("utf-8")

    with LAST_IMAGE_LOCK:
        LAST_IMAGE_BY_THREAD_ID[thread_id] = {
            "b64_data": b64_data,
            "mime_type": image.get("mime_type", "image/png"),
        }


def build_json_response(result: dict):
    return {
        "success": result["success"],
        "model": result["model"],
        "prompt": result["prompt"],
        "input_image_count": result["input_image_count"],
        "max_input_images": result["max_input_images"],
        "image_count": result["image_count"],
        "text": result["text"],
        "images": [
            {
                "filename": img["filename"],
                "mime_type": img["mime_type"],
                "b64_data": base64.b64encode(img["data"]).decode("utf-8"),
            }
            for img in result["images"]
        ],
    }


@app.route("/images", methods=["POST"])
def images():
    try:
        prompt = request.form.get("message", "").strip()
        thread_id = (request.form.get("id") or "").strip()

        input_images_b64, input_mime_type = extract_images_from_request()

        # Si aucune image n'est envoyée, on tente de réutiliser la dernière image du thread
        if not input_images_b64 and thread_id:
            last_image = get_last_image_for_thread(thread_id)
            if last_image:
                input_images_b64 = [last_image["b64_data"]]
                input_mime_type = last_image["mime_type"]

        result = generate_image(
            prompt=prompt,
            input_images_b64=input_images_b64 or None,
            input_mime_type=input_mime_type or "image/png",
            client=gemini_client,
            model=request.form.get("model", "gemini-3.1-flash-image-preview"),
            aspect_ratio=request.form.get("aspect_ratio", "1:1"),
            image_size=request.form.get("image_size", "1K"),
            thinking_level=request.form.get("thinking_level", "HIGH"),
            person_generation=request.form.get("person_generation") or None,
            use_google_image_search=request.form.get("use_google_image_search", "false").lower() == "true",
            file_prefix=request.form.get("file_prefix", "image"),
            max_input_images=int(request.form.get("max_input_images", 10)),
        )

        if thread_id and result.get("images"):
            set_last_image_for_thread(thread_id, result["images"][0])

        return jsonify(build_json_response(result)), 200

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": f"Entrée invalide: {str(e)}",
        }), 400

    except RuntimeError as e:
        return jsonify({
            "success": False,
            "error": f"Erreur génération image: {str(e)}",
        }), 500

    except Exception:
        return jsonify({
            "success": False,
            "error": "Erreur interne inattendue",
        }), 500


@app.route("/new_images", methods=["POST"])
def new_images():
    try:
        prompt = request.form.get("message", "").strip()
        input_images_b64, input_mime_type = extract_images_from_request()

        result = generate_image(
            prompt=prompt,
            input_images_b64=input_images_b64 or None,
            input_mime_type=input_mime_type or "image/png",
            client=gemini_client,
            model=request.form.get("model", "gemini-3.1-flash-image-preview"),
            aspect_ratio=request.form.get("aspect_ratio", "1:1"),
            image_size=request.form.get("image_size", "1K"),
            thinking_level=request.form.get("thinking_level", "HIGH"),
            person_generation=request.form.get("person_generation") or None,
            use_google_image_search=request.form.get("use_google_image_search", "false").lower() == "true",
            file_prefix=request.form.get("file_prefix", "new_image"),
            max_input_images=int(request.form.get("max_input_images", 10)),
        )

        return jsonify(build_json_response(result)), 200

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": f"Entrée invalide: {str(e)}",
        }), 400

    except RuntimeError as e:
        return jsonify({
            "success": False,
            "error": f"Erreur génération image: {str(e)}",
        }), 500

    except Exception:
        return jsonify({
            "success": False,
            "error": "Erreur interne inattendue",
        }), 500
        
@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}
    

if __name__ == "__main__":
    port = int(settings.PORT)
    app.run(host="0.0.0.0", port=port, debug=False)
