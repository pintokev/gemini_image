import os
import mimetypes
from typing import Optional

from google import genai
from google.genai import types

from config import DEFAULT_MAX_INPUT_IMAGES, DEFAULT_MODEL
from utils import decode_b64_image, sanitize_filename
from validators import (
    validate_input_images_count,
    validate_params,
    validate_prompt,
)


def build_tools(use_google_image_search: bool):
    if not use_google_image_search:
        return None

    return [
        types.Tool(
            googleSearch=types.GoogleSearch(
                search_types=types.SearchTypes(
                    image_search=types.ImageSearch(),
                ),
            )
        )
    ]


def build_image_part_from_b64(
        b64_data: str,
        mime_type: str = "image/png",
):
    return types.Part.from_bytes(
        mime_type=mime_type,
        data=decode_b64_image(b64_data),
    )


def generate_image(
        prompt: str,
        input_images_b64: Optional[list[str]] = None,
        input_mime_type: str = "image/png",
        model: str = DEFAULT_MODEL,
        api_key: Optional[str] = None,
        client: Optional[genai.Client] = None,
        aspect_ratio: str = "1:1",
        image_size: str = "1K",
        thinking_level: str = "HIGH",
        person_generation: Optional[str] = None,
        use_google_image_search: bool = False,
        file_prefix: str = "generated_image",
        max_input_images: int = DEFAULT_MAX_INPUT_IMAGES,
) -> dict:
    validate_prompt(prompt)

    validate_params(
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        thinking_level=thinking_level,
        input_mime_type=input_mime_type,
    )

    validate_input_images_count(
        input_images_b64=input_images_b64,
        max_input_images=max_input_images,
    )

    if client is None:
        api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY manquante")
        client = genai.Client(api_key=api_key)

    parts = []

    if input_images_b64:
        for b64_data in input_images_b64:
            parts.append(
                build_image_part_from_b64(
                    b64_data=b64_data,
                    mime_type=input_mime_type,
                )
            )

    parts.append(types.Part.from_text(text=prompt))

    contents = [
        types.Content(
            role="user",
            parts=parts,
        ),
    ]

    image_config_kwargs = {
        "aspect_ratio": aspect_ratio,
        "image_size": image_size,
    }

    if person_generation is not None:
        image_config_kwargs["person_generation"] = person_generation

    config_kwargs = {
        "thinking_config": types.ThinkingConfig(
            thinking_level=thinking_level,
        ),
        "image_config": types.ImageConfig(**image_config_kwargs),
        "response_modalities": ["IMAGE"],
    }

    tools = build_tools(use_google_image_search)
    if tools:
        config_kwargs["tools"] = tools

    generate_content_config = types.GenerateContentConfig(**config_kwargs)

    images = []
    text_chunks = []

    try:
        for chunk in client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
        ):
            if not getattr(chunk, "parts", None):
                if getattr(chunk, "text", None):
                    text_chunks.append(chunk.text)
                continue

            for part in chunk.parts:
                inline_data = getattr(part, "inline_data", None)

                if inline_data and getattr(inline_data, "data", None):
                    mime_type = inline_data.mime_type or "application/octet-stream"
                    extension = mimetypes.guess_extension(mime_type) or ".bin"
                    filename = f"{sanitize_filename(file_prefix)}_{len(images)}{extension}"

                    images.append({
                        "filename": filename,
                        "mime_type": mime_type,
                        "data": inline_data.data,
                    })

                elif getattr(part, "text", None):
                    text_chunks.append(part.text)

    except Exception as e:
        raise RuntimeError(f"Erreur pendant la génération d'image: {e}") from e

    return {
        "success": True,
        "model": model,
        "prompt": prompt,
        "input_image_count": len(input_images_b64 or []),
        "max_input_images": max_input_images,
        "images": images,
        "text": "".join(text_chunks).strip(),
        "image_count": len(images),
    }