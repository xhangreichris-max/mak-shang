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
    Reads GEMINI_API_KEY from .env.
"""

import sys, json, base64, os
import urllib.request, urllib.error

PIPELINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Appended to every prompt — describes brand aesthetic constraints, never a specific image.
BRAND_DIRECTIVE = (
    " Original AI-generated interior lifestyle photograph. "
    "Square 1:1 format — compose the scene to fill a square frame with no letterboxing or portrait/landscape cropping. "
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


def _try_model(prompt, output_path, model, key):
    # Gemini image models use the Interactions API, not generateContent.
    url = "https://generativelanguage.googleapis.com/v1beta/interactions"
    body = json.dumps({
        "model": model,
        "input": [{"type": "text", "text": prompt + BRAND_DIRECTIVE}],
        "response_format": {"type": "image", "mime_type": "image/jpeg"},
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json", "X-goog-api-key": key},
    )
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=150).read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"  {model}: HTTP {e.code} {e.read().decode('utf-8', 'ignore')[:200]}")
        return False
    except Exception as e:
        print(f"  {model}: {e}")
        return False

    # Top-level output_image (documented) or nested in steps[].content[] (actual API behavior).
    data = (r.get("output_image") or {}).get("data")
    if not data:
        for step in r.get("steps", []):
            for part in step.get("content", []):
                if part.get("data") and (part.get("mime_type", "").startswith("image/") or part.get("type") == "image"):
                    data = part["data"]
                    break
            if data:
                break
    if data:
        with open(output_path, "wb") as f:
            f.write(base64.b64decode(data))
        print(f"  Saved {output_path} ({os.path.getsize(output_path):,} bytes) via {model}")
        return True
    print(f"  {model}: no image data in response — {str(r)[:200]}")
    return False


def generate_ai_image(prompt, output_path, model="gemini-3-pro-image"):
    """
    Generate a MAK-SHANG brand lifestyle image using Gemini.
    Returns True if the PNG was saved, False otherwise.
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
