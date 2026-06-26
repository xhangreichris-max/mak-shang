#!/usr/bin/env python3
"""
Tool: render_swatch_overlay  (Format A — Swatch + Lifestyle Overlay)

Composites a color-swatch label box and headline over a lifestyle photo background,
then captures a 1080x1080 PNG via Puppeteer.

Primary function:
    render_swatch_overlay(
        background_image_path: str,
        overlay_data: dict,
        output_slug: str,
    ) -> str | None

    background_image_path: absolute path to the AI-generated lifestyle photo (PNG)
    overlay_data: dict with keys:
        "color_hex"     (str)  — CSS hex color for the swatch square, e.g. "#C4926A"
        "color_name"    (str)  — human-readable color name, e.g. "Terracotta Clay"
        "color_ref"     (str)  — MAK-SHANG reference code, e.g. "MS-TC-04" (or "" to omit)
        "headline"      (str)  — 2-5 word headline, uppercase in output
        "footer_handle" (str)  — Instagram handle, e.g. "@makshangpaints"
    output_slug: short string used in the output filename,
        e.g. "20260625_1_trend-spotlight"

    Returns: absolute path to the rendered PNG, or None if rendering failed.
    Writes intermediate HTML to generated_images/.

Requires: Node.js + Puppeteer installed; cap_infographic.js in the pipeline dir.
"""

import json, os, sys, subprocess

PIPELINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(PIPELINE_DIR, "swatch_overlay_template.html")
NODE_SCRIPT = os.path.join(PIPELINE_DIR, "cap_infographic.js")


def _logo_url():
    logo = os.path.join(PIPELINE_DIR, "assets", "logo.png")
    return "file:///" + logo.replace("\\", "/")


def _image_url(image_path):
    return "file:///" + os.path.abspath(image_path).replace("\\", "/")


def _render_html(background_image_path, overlay_data, out_html_path):
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        html = f.read()

    html = html.replace("{{BG_IMAGE_URL}}", _image_url(background_image_path))
    html = html.replace("{{COLOR_HEX}}", overlay_data.get("color_hex", "#C4B8A8"))
    html = html.replace("{{COLOR_NAME}}", overlay_data.get("color_name", ""))
    html = html.replace("{{COLOR_REF}}", overlay_data.get("color_ref", ""))
    html = html.replace("{{HEADLINE}}", overlay_data.get("headline", ""))
    html = html.replace("{{FOOTER_HANDLE}}", overlay_data.get("footer_handle", "@makshangpaints"))
    html = html.replace("{{LOGO_URL}}", _logo_url())

    with open(out_html_path, "w", encoding="utf-8") as f:
        f.write(html)


def _capture_png(html_path, png_path):
    if not os.path.exists(NODE_SCRIPT):
        print(f"ERROR: cap_infographic.js not found at {NODE_SCRIPT}")
        return False
    result = subprocess.run(
        ["node", NODE_SCRIPT, html_path, png_path],
        capture_output=True, text=True, cwd=PIPELINE_DIR,
    )
    if result.returncode != 0:
        print(f"Puppeteer error: {result.stderr[:300]}")
        return False
    print(f"PNG saved: {png_path}")
    return True


def render_swatch_overlay(background_image_path, overlay_data, output_slug):
    """
    Composite a swatch + headline overlay onto a lifestyle photo and capture PNG.
    Returns the absolute path to the PNG, or None on failure.
    """
    out_dir = os.path.join(PIPELINE_DIR, "generated_images")
    os.makedirs(out_dir, exist_ok=True)
    html_path = os.path.join(out_dir, f"swatch_overlay_{output_slug}.html")
    png_path = os.path.join(out_dir, f"swatch_overlay_{output_slug}.png")

    _render_html(background_image_path, overlay_data, html_path)
    success = _capture_png(html_path, png_path)
    return png_path if success else None


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("usage: python tools/render_swatch_overlay.py <bg_image.png> <overlay_data.json> <output_slug>")
        sys.exit(1)
    bg_path = sys.argv[1]
    with open(sys.argv[2], encoding="utf-8") as f:
        data = json.load(f)
    result = render_swatch_overlay(bg_path, data, sys.argv[3])
    print(result or "FAILED")
    sys.exit(0 if result else 1)
