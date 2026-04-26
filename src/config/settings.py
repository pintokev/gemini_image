import os
from src.config.get_secrets import get_config

ALLOWED_IMAGE_SIZES = {"1K", "2K"}
ALLOWED_ASPECT_RATIOS = {"1:1", "16:9", "9:16", "4:3", "3:4"}
ALLOWED_THINKING_LEVELS = {"LOW", "MEDIUM", "HIGH"}
ALLOWED_INPUT_MIME_TYPES = {"image/png", "image/jpeg", "image/webp"}

DEFAULT_MODEL = "gemini-3.1-flash-image-preview"
DEFAULT_MAX_INPUT_IMAGES = 10
DEFAULT_MAX_PROMPT_LENGTH = 5000

PORT = os.environ.get("PORT", 8080)
INTERNAL_API_TOKEN = get_config("INTERNAL_API_TOKEN", required=False)

GEMINI_API_KEY = get_config("GEMINI_API_KEY", "tokenGemini-prd")
