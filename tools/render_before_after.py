#!/usr/bin/env python3
"""
Tool: render_before_after  (Format C — Before/After Split)

Composites a split-panel before/after card from a single AI-generated "after" image.
The "before" panel is the same image with a CSS desaturation/darkening filter applied —
no second image generation call needed. Captures a 1080x1080 PNG via Puppeteer.

Primary function:
    render_before_after(
        after_image_path: str,
        before_after_data: dict,
        output_slug: str,
    ) -> str | None

    after_image_path: absolute path to the AI-generated "after" lifestyle photo (PNG)
    before_after_data: dict with keys:
        "headline"       (str) — optional short headline shown above the panels (2–6 words).
                                  Omit or set to "" to show panels only with no headline bar.
        "headline_accent" (str) — optional word within the headline to render in red italic.
                                   Only used when "headline" is present. Set to "" to skip.
        "footer_handle"  (str) — Instagram handle, e.g. "@makshangpaints"
        "footer_tagline" (str) — short tagline for footer, e.g. "MAK-SHANG Paints · Ukhrul"
    output_slug: short string used in the output filename,
        e.g. "20260625_2_local-adaptation"

    Returns: absolute path to the rendered PNG, or None if rendering failed.
    Writes intermediate HTML to generated_images/.

    Implementation note: the "before" panel is a CSS-filtered duplicate of the after image
    (grayscale + darkened), not a separately generated image. This is intentional — it avoids
    AI consistency problems across two separately generated scenes, and produces clean,
    predictable before/after contrast without a second Gemini call.

Requires: Node.js + Puppeteer installed; cap_infographic.js in the pipeline dir.
"""

import json, os, sys, subprocess

PIPELINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(PIPELINE_DIR, "before_after_template.html")
NODE_SCRIPT = os.path.join(PIPELINE_DIR, "cap_infographic.js")


def _logo_url():
    logo = os.path.join(PIPELINE_DIR, "assets", "logo.png")
    return "file:///" + logo.replace("\\", "/")


def _image_url(image_path):
    return "file:///" + os.path.abspath(image_path).replace("\\", "/")


def _render_html(after_image_path, before_after_data, out_html_path):
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        html = f.read()

    headline = before_after_data.get("headline", "")
    if headline:
        accent = before_after_data.get("headline_accent", "")
        if accent and accent in headline:
            hl_html = headline.replace(
                accent,
                f'<span class="headline-accent">{accent}</span>',
                1,
            )
        else:
            hl_html = headline
        headline_block = f'<div class="headline-bar"><div class="headline-text">{hl_html}</div></div>'
        # Push label chips below the headline bar (approx 88px tall with padding + border)
        label_top = 96
    else:
        headline_block = ""
        label_top = 22

    html = html.replace("{{AFTER_IMAGE_URL}}", _image_url(after_image_path))
    html = html.replace("{{PANEL_LABEL_TOP}}", str(label_top))
    html = html.replace("{{HEADLINE_BLOCK}}", headline_block)
    html = html.replace("{{FOOTER_HANDLE}}", before_after_data.get("footer_handle", "@makshangpaints"))
    html = html.replace("{{FOOTER_TAGLINE}}", before_after_data.get("footer_tagline", "MAK-SHANG Paints · Ukhrul"))
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


def render_before_after(after_image_path, before_after_data, output_slug):
    """
    Build a before/after split panel card from a single image and capture PNG.
    Returns the absolute path to the PNG, or None on failure.
    """
    out_dir = os.path.join(PIPELINE_DIR, "generated_images")
    os.makedirs(out_dir, exist_ok=True)
    html_path = os.path.join(out_dir, f"before_after_{output_slug}.html")
    png_path = os.path.join(out_dir, f"before_after_{output_slug}.png")

    _render_html(after_image_path, before_after_data, html_path)
    success = _capture_png(html_path, png_path)
    return png_path if success else None


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("usage: python tools/render_before_after.py <after_image.png> <data.json> <output_slug>")
        sys.exit(1)
    img_path = sys.argv[1]
    with open(sys.argv[2], encoding="utf-8") as f:
        data = json.load(f)
    result = render_before_after(img_path, data, sys.argv[3])
    print(result or "FAILED")
    sys.exit(0 if result else 1)
