#!/usr/bin/env python3
"""
Tool: render_infographic

Fills the MAK-SHANG infographic HTML template with structured JSON data, then
captures a 1080x1080 PNG using Puppeteer (cap_infographic.js).

Primary function:
    render_infographic(infographic_data: dict, output_slug: str) -> str | None

    infographic_data: structured dict produced by the agent's reasoning step.
        "ranked_bars" format: {"format", "title_main", "title_span", "subtitle",
            "badge", "date_label", "takeaway_num", "takeaway_text", "source",
            "bars": [{"label", "value", "color"}, ...]}
        "hero_number" format: {"format", "title_main", "title_span", "subtitle",
            "badge", "date_label", "hero_number", "hero_label",
            "checklist": [str, ...], "source"}

    output_slug: short string used in the output filenames,
        e.g. "20260624_1_comparison"

    Returns: absolute path to the rendered PNG, or None if rendering failed.
    Also writes an intermediate .html file alongside the PNG.

Requires: Node.js + Puppeteer installed; cap_infographic.js present in the pipeline dir.
"""

import json, os, sys, subprocess

PIPELINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(PIPELINE_DIR, "infographic_template.html")
NODE_SCRIPT = os.path.join(PIPELINE_DIR, "cap_infographic.js")

BAR_COLORS = ["#E02020", "#0A0A0A", "#6E6E6E", "#C4B8A8", "#8B7355"]


def _build_bars_block(data):
    bars = data.get("bars", [])
    rows = []
    for i, bar in enumerate(bars):
        color = bar.get("color") or BAR_COLORS[i % len(BAR_COLORS)]
        value = bar.get("value", "50%")
        width = value if value.endswith("%") else f"{value}%"
        row = f"""<div class="bar-row">
      <div class="bar-info">
        <span class="bar-label">{bar.get('label', '')}</span>
        <span class="bar-value">{value}</span>
      </div>
      <div class="bar-track">
        <div class="bar-fill" style="width:{width}; background:{color};"></div>
      </div>
    </div>"""
        rows.append(row)

    takeaway_num = data.get("takeaway_num", "")
    takeaway_text = data.get("takeaway_text", "")
    bars_html = "\n    ".join(rows)

    return f"""<div class="content-bars">
    {bars_html}
  </div>
  <div class="takeaway-box">
    <div class="takeaway-text"><span class="takeaway-num">{takeaway_num}</span> {takeaway_text}</div>
  </div>"""


def _build_hero_block(data):
    hero_number = data.get("hero_number", "5")
    hero_label = data.get("hero_label", "things to check")
    checklist = data.get("checklist", [])
    items_html = "\n    ".join(
        f'<div class="checklist-item"><div class="check-box"></div><span>{item}</span></div>'
        for item in checklist
    )
    return f"""<div class="content-hero">
    <div class="hero-stat-row">
      <div class="hero-number">{hero_number}</div>
      <div class="hero-label">{hero_label}</div>
    </div>
    <div class="checklist">
      {items_html}
    </div>
  </div>"""


def _logo_url():
    logo = os.path.join(PIPELINE_DIR, "assets", "logo.png")
    return "file:///" + logo.replace("\\", "/")


def _render_html(data, out_html_path):
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        template = f.read()

    fmt = data.get("format", "ranked_bars")
    content_block = _build_hero_block(data) if fmt == "hero_number" else _build_bars_block(data)

    html = template
    html = html.replace("{{BADGE}}", data.get("badge", "🎨 PAINT GUIDE"))
    html = html.replace("{{DATE_LABEL}}", data.get("date_label", "MAK-SHANG 2026"))
    html = html.replace("{{TITLE_MAIN}}", data.get("title_main", ""))
    html = html.replace("{{TITLE_SPAN}}", data.get("title_span", ""))
    html = html.replace("{{SUBTITLE}}", data.get("subtitle", ""))
    html = html.replace("{{CONTENT_BLOCK}}", content_block)
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


def render_infographic(infographic_data, output_slug):
    """
    Fill the HTML template with infographic_data and capture a PNG via Puppeteer.
    Returns the absolute path to the PNG, or None on failure.
    """
    out_dir = os.path.join(PIPELINE_DIR, "generated_images")
    os.makedirs(out_dir, exist_ok=True)
    html_path = os.path.join(out_dir, f"infographic_{output_slug}.html")
    png_path = os.path.join(out_dir, f"infographic_{output_slug}.png")

    _render_html(infographic_data, html_path)
    success = _capture_png(html_path, png_path)
    return png_path if success else None


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: python tools/render_infographic.py <data.json> <output_slug>")
        sys.exit(1)
    with open(sys.argv[1], encoding="utf-8") as f:
        data = json.load(f)
    result = render_infographic(data, sys.argv[2])
    print(result or "FAILED")
    sys.exit(0 if result else 1)
