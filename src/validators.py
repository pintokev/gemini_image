from src.config import (
    ALLOWED_ASPECT_RATIOS,
    ALLOWED_IMAGE_SIZES,
    ALLOWED_INPUT_MIME_TYPES,
    ALLOWED_THINKING_LEVELS,
    DEFAULT_MAX_PROMPT_LENGTH,
)


def validate_prompt(prompt: str, max_prompt_length: int = DEFAULT_MAX_PROMPT_LENGTH) -> None:
    if not prompt or not prompt.strip():
        raise ValueError("Le prompt ne peut pas être vide")

    if len(prompt) > max_prompt_length:
        raise ValueError(
            f"Prompt trop long: {len(prompt)} caractères, maximum autorisé: {max_prompt_length}"
        )


def validate_params(
    aspect_ratio: str,
    image_size: str,
    thinking_level: str,
    input_mime_type: str,
) -> None:
    if aspect_ratio not in ALLOWED_ASPECT_RATIOS:
        raise ValueError(f"aspect_ratio invalide: {aspect_ratio}")

    if image_size not in ALLOWED_IMAGE_SIZES:
        raise ValueError(f"image_size invalide: {image_size}")

    if thinking_level not in ALLOWED_THINKING_LEVELS:
        raise ValueError(f"thinking_level invalide: {thinking_level}")

    if input_mime_type not in ALLOWED_INPUT_MIME_TYPES:
        raise ValueError(f"input_mime_type invalide: {input_mime_type}")


def validate_input_images_count(
    input_images_b64: list[str] | None,
    max_input_images: int,
) -> None:
    if max_input_images < 1:
        raise ValueError("max_input_images doit être >= 1")

    image_count = len(input_images_b64 or [])
    if image_count > max_input_images:
        raise ValueError(
            f"Trop d'images en entrée: {image_count} reçues, maximum autorisé: {max_input_images}"
        )
