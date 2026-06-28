#!/usr/bin/env python3
"""
Tool: generate_ai_image

Calls the Gemini image generation API to produce an on-brand AI lifestyle photo
for MAK-SHANG. The MAK-SHANG brand directive (aesthetic constraints, no text/logos)
is appended to every prompt automatically.

Primary function:
    generate_ai_image(prompt: str, output_path: str, model: str = "gemini-3-pro-image") -> bool

    prompt:       the image concept from the agent's reasoning step (under 120 words)
    output_path:  absolute path where the PNG should be saved
    model:        Gemini model to try first; falls back to gemini-2.5-flash-image on failure

    Returns True if the image was saved successfully, False otherwise.
    Reads GEMINI_API_KEY from .env or environment.
"""

import sys, base64, os, struct

PIPELINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Appended to every prompt — describes brand aesthetic constraints, never a specific image.
BRAND_DIRECTIVE = (
    " Original AI-generated interior lifestyle photograph. "
    "4:5 portrait format — compose the scene to fill a 1080x1350 vertical frame with no letterboxing or square/landscape cropping. "
    "Warm bone/cream background tones (#F4F0E8). "
    "MAK-SHANG Paints brand aesthetic: international design sensibility rooted in NE India. "
    "Tangkhul Naga cultural warmth — natural materials, handwoven textiles, warm light. "
    "Clean, editorial composition with generous negative space. "
    "Aspirational but livable — not sterile or generic. "
    "No text, no words, no letters, no logos, no watermarks in the image."
)


def _load_key():
    env_path = os.path.join(PIPELINE_DIR, ".env")
    try:
        with open(env_path) as f:
            for line in f:
                if line.startswith("GEMINI_API_KEY="):
                    return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return os.environ.get("GEMINI_API_KEY", "")


def _image_dimensions(path):
    """Read pixel dimensions from PNG or JPEG without external libs."""
    try:
        with open(path, "rb") as f:
            data = f.read(65536)  # enough to find JPEG SOF in any reasonable header
        # PNG
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            w, h = struct.unpack(">II", data[16:24])
            return w, h
        # JPEG — scan for SOF0/SOF1/SOF2 marker
        if data[:2] == b"\xff\xd8":
            i = 2
            while i < len(data) - 8:
                if data[i] != 0xFF:
                    break
                marker = data[i + 1]
                if marker in (0xC0, 0xC1, 0xC2):
                    h, w = struct.unpack(">HH", data[i + 5 : i + 9])
                    return w, h
                seg_len = struct.unpack(">H", data[i + 2 : i + 4])[0]
                i += 2 + seg_len
    except Exception:
        pass
    return None, None


def _try_model(prompt, output_path, model, key):
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("  ERROR: google-genai not installed — run: pip install google-genai")
        return False

    client = genai.Client(api_key=key)
    full_prompt = prompt + BRAND_DIRECTIVE

    # Build generation config with explicit 4:5 aspect ratio.
    # types.ImageConfig is the image-generation config accepted by Gemini image models.
    # If the model silently ignores this, _image_dimensions() will reveal it.
    try:
        config = types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="4:5"),
        )
    except AttributeError as e:
        # SDK version mismatch — ImageConfig class name may differ; show what's available.
        image_types = [x for x in dir(types) if "image" in x.lower() or "Image" in x]
        print(f"  WARNING: {e}")
        print(f"  Available image-related types in this SDK version: {image_types}")
        # Fall back to config without aspect_ratio so at least we get an image
        config = types.GenerateContentConfig(response_modalities=["IMAGE"])

    try:
        response = client.models.generate_content(
            model=model,
            contents=full_prompt,
            config=config,
        )
    except Exception as e:
        print(f"  {model}: {e}")
        return False

    # Extract image bytes from response parts
    data = None
    if response.candidates:
        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data:
                data = part.inline_data.data
                break

    if not data:
        # Print full response structure so the caller can diagnose what came back
        print(f"  {model}: no image data in response")
        if response.candidates:
            cand = response.candidates[0]
            print(f"  finish_reason={cand.finish_reason}")
            for i, p in enumerate(cand.content.parts):
                has_img = hasattr(p, "inline_data") and p.inline_data is not None
                print(f"  part[{i}]: {type(p).__name__}, inline_data={has_img}, text={getattr(p, 'text', '')[:80]!r}")
        else:
            print(f"  raw response: {response}")
        return False

    # SDK returns bytes directly; raw REST API returns base64 string — handle both.
    raw = data if isinstance(data, (bytes, bytearray)) else base64.b64decode(data)
    with open(output_path, "wb") as f:
        f.write(raw)

    size = os.path.getsize(output_path)
    w, h = _image_dimensions(output_path)
    ratio = f" ({w/h:.3f} ratio)" if w and h else ""
    dim_str = f"{w}x{h}{ratio}" if w else "unknown dimensions"
    print(f"  Saved {output_path} ({size:,} bytes) | {dim_str} | via {model}")
    return True


def generate_ai_image(prompt, output_path, model="gemini-3-pro-image"):
    """
    Generate a MAK-SHANG brand lifestyle image using Gemini.
    Returns True if the image was saved, False otherwise.
    """
    key = _load_key()
    if not key:
        print("ERROR: GEMINI_API_KEY not set in .env")
        return False

    if _try_model(prompt, output_path, model, key):
        return True
    if model != "gemini-2.5-flash-image":
        print("  -> falling back to gemini-2.5-flash-image")
        return _try_model(prompt, output_path, "gemini-2.5-flash-image", key)
    return False


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('usage: python tools/generate_ai_image.py "<prompt>" <out.png> [model]')
        sys.exit(1)
    prompt_arg = sys.argv[1]
    out_arg = sys.argv[2]
    model_arg = sys.argv[3] if len(sys.argv) > 3 else "gemini-3-pro-image"
    sys.exit(0 if generate_ai_image(prompt_arg, out_arg, model_arg) else 1)
