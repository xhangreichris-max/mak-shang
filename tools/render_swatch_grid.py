#!/usr/bin/env python3
"""
Tool: render_swatch_grid  (Format B — Shade/Material Grid)

Renders a color-swatch comparison card as a 1080x1080 PNG via Puppeteer.
Uses no AI-generated image — pure HTML/CSS layout, same pipeline as render_infographic.

Primary function:
    render_swatch_grid(swatch_data: dict, output_slug: str) -> str | None

    swatch_data: structured dict matching the swatch_grid schema:
        {
            "format":     "swatch_grid",
            "title_main": "Short punchy title (2–4 words)",
            "title_span": "accent word shown in red",
            "subtitle":   "One sentence — max 12 words",
            "badge":      "🎨 FINISH GUIDE",
            "date_label": "MAK-SHANG 2026",
            "source":     "Source: MAK-SHANG Paints | @makshangpaints",
            "swatches": [
                {"color_hex": "#E02020", "label": "High-Gloss", "sublabel": "Sheen: 60–80%"},
                {"color_hex": "#0A0A0A", "label": "Satin",      "sublabel": "Sheen: 20–40%"},
                {"color_hex": "#6E6E6E", "label": "Matte",      "sublabel": "Sheen: <5%"}
            ],
            "footnote": "Optional short note"   (omit or "" to hide)
        }
        Include 3–5 swatches for best visual balance.

    output_slug: short string used in output filenames,
        e.g. "20260625_2_comparison"

    Returns: absolute path to the rendered PNG, or None if rendering failed.
    Also writes an intermediate .html file to generated_images/.

Requires: Node.js + Puppeteer installed; cap_infographic.js in the pipeline dir.
"""

import json, os, sys, subprocess

PIPELINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(PIPELINE_DIR, "swatch_grid_template.html")
NODE_SCRIPT = os.path.join(PIPELINE_DIR, "cap_infographic.js")


def _logo_url():
    logo = os.path.join(PIPELINE_DIR, "assets", "logo.png")
    return "file:///" + logo.replace("\\", "/")


def _build_swatch_cols(data):
    swatches = data.get("swatches", [])
    cols = []
    for sw in swatches:
        color = sw.get("color_hex", "#C4B8A8")
        label = sw.get("label", "")
        sublabel = sw.get("sublabel", "")
        col = f"""<div class="swatch-col">
      <div class="swatch-block" style="background:{color};"></div>
      <div class="swatch-info">
        <div class="swatch-label">{label}</div>
        <div class="swatch-sublabel">{sublabel}</div>
      </div>
    </div>"""
        cols.append(col)
    return "\n    ".join(cols)


def _render_html(data, out_html_path):
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        html = f.read()

    footnote = data.get("footnote", "")
    footnote_block = (
        f'<div class="footnote">{footnote}</div>' if footnote else ""
    )

    html = html.replace("{{BADGE}}", data.get("badge", "🎨 FINISH GUIDE"))
    html = html.replace("{{DATE_LABEL}}", data.get("date_label", "MAK-SHANG 2026"))
    html = html.replace("{{TITLE_MAIN}}", data.get("title_main", ""))
    html = html.replace("{{TITLE_SPAN}}", data.get("title_span", ""))
    html = html.replace("{{SUBTITLE}}", data.get("subtitle", ""))
    html = html.replace("{{SWATCH_COLS}}", _build_swatch_cols(data))
    html = html.replace("{{FOOTNOTE_BLOCK}}", footnote_block)
    html = html.replace("{{SOURCE}}", data.get("source", "Source: MAK-SHANG Paints | @makshangpaints"))
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


def render_swatch_grid(swatch_data, output_slug):
    """
    Fill the swatch grid HTML template and capture a PNG via Puppeteer.
    Returns the absolute path to the PNG, or None on failure.
    """
    out_dir = os.path.join(PIPELINE_DIR, "generated_images")
    os.makedirs(out_dir, exist_ok=True)
    html_path = os.path.join(out_dir, f"swatch_grid_{output_slug}.html")
    png_path = os.path.join(out_dir, f"swatch_grid_{output_slug}.png")

    _render_html(swatch_data, html_path)
    success = _capture_png(html_path, png_path)
    return png_path if success else None


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: python tools/render_swatch_grid.py <data.json> <output_slug>")
        sys.exit(1)
    with open(sys.argv[1], encoding="utf-8") as f:
        data = json.load(f)
    result = render_swatch_grid(data, sys.argv[2])
    print(result or "FAILED")
    sys.exit(0 if result else 1)
