#!/usr/bin/env python3
"""
MCP server for the MAK-SHANG content pipeline.

Exposes all pipeline tool functions as MCP tools for Antigravity 2.0.
Internal tool logic lives in the individual tool files — this file only imports
and wraps them. No business logic lives here.

Install dependency: pip install fastmcp
Run (stdio transport, for MCP clients): python3 tools/mcp_server.py
"""

import sys
import os
from pathlib import Path
from typing import Optional

# Put tools/ on the import path so the sibling modules resolve cleanly
TOOLS_DIR = Path(__file__).parent
sys.path.insert(0, str(TOOLS_DIR))

from fastmcp import FastMCP

from fetch_trends import fetch_trends as _fetch_trends
from read_rotation_log import read_rotation_log as _read_rotation_log
from write_rotation_log import write_rotation_log as _write_rotation_log
from generate_ai_image import generate_ai_image as _generate_ai_image
from render_infographic import render_infographic as _render_infographic
from render_swatch_overlay import render_swatch_overlay as _render_swatch_overlay
from render_swatch_grid import render_swatch_grid as _render_swatch_grid
from render_before_after import render_before_after as _render_before_after
from upload_to_github import upload_to_github as _upload_to_github
from post_to_instagram import post_to_instagram as _post_to_instagram
from post_to_facebook import post_to_facebook as _post_to_facebook

mcp = FastMCP("mak-shang-pipeline")


@mcp.tool()
def fetch_trends() -> list:
    """
    Fetch fresh paint and interior-design trend candidates from Brave Search and RSS feeds.
    Deduplicates against recently covered topics in trend-topic-log.json.

    Returns a list of candidate dicts:
        {"title": str, "url": str, "snippet": str, "source": str, "published_date": str}

    Also writes the result to trend_candidates.json in the pipeline directory.
    Reads BRAVE_SEARCH_API_KEY from environment (optional; RSS-only fallback if absent).
    Raises RuntimeError if fewer than 3 fresh candidates are found.
    """
    try:
        return _fetch_trends()
    except SystemExit as e:
        raise RuntimeError(
            f"fetch_trends exited with code {e.code}: "
            "fewer than 3 fresh candidates found — check RSS sources or clear the topic log"
        )


@mcp.tool()
def read_rotation_log() -> dict:
    """
    Read the archetype rotation log and topic dedup log from the pipeline directory.
    Computes which archetypes are due today using least-recently-used order.

    Returns a dict:
        {
            "archetype_log": list,       # full contents of archetype-rotation-log.json
            "topic_log": list,            # full contents of trend-topic-log.json
            "due_archetypes": list[str],  # 3 archetype names, most overdue first
        }

    No API keys required. Reads local JSON files only. Safe to call on first run (empty logs).
    """
    return _read_rotation_log()


@mcp.tool()
def write_rotation_log(posts: list) -> bool:
    """
    Append today's published posts to the archetype rotation log and topic dedup log.
    Caps the archetype log at 60 entries and the topic log at 90 entries.
    Call once at the very end of each daily run, after all posts are published.

    posts: list of post dicts, each containing:
        "archetype"    (str) — the assigned archetype name
        "source_title" (str) — the original source article title
        "date"         (str) — ISO date string YYYY-MM-DD

    Returns True on success, False on failure.
    No API keys required. Reads/writes local JSON files only.
    """
    return _write_rotation_log(posts)


@mcp.tool()
def generate_ai_image(
    prompt: str,
    output_path: str,
    model: str = "gemini-3-pro-image",
) -> bool:
    """
    Generate an on-brand AI lifestyle photo for MAK-SHANG using the Gemini image API.
    The MAK-SHANG brand directive (aesthetic constraints, no text/logos) is appended
    to every prompt automatically — do not repeat it in the prompt you supply.
    Falls back to gemini-2.5-flash-image automatically if the primary model fails.

    prompt:       image concept from the agent's reasoning step (under 120 words)
    output_path:  absolute path where the PNG should be saved
    model:        Gemini model to try first (default: gemini-3-pro-image)

    Returns True if the PNG was saved successfully, False otherwise.
    Reads GEMINI_API_KEY from environment.
    """
    return _generate_ai_image(prompt, output_path, model)


@mcp.tool()
def render_infographic(infographic_data: dict, output_slug: str) -> Optional[str]:
    """
    Fill the MAK-SHANG infographic HTML template with structured JSON data and capture
    a 1080x1080 PNG via Puppeteer (cap_infographic.js must be present in the pipeline dir).

    infographic_data must match one of two schemas:
        "ranked_bars" (Comparison / Cost & Care Guide):
            {"format": "ranked_bars", "title_main", "title_span", "subtitle", "badge",
             "date_label", "takeaway_num", "takeaway_text", "source",
             "bars": [{"label", "value", "color"}, ...]}
        "hero_number" (Before You Paint):
            {"format": "hero_number", "title_main", "title_span", "subtitle", "badge",
             "date_label", "hero_number", "hero_label", "checklist": [str, ...], "source"}

    output_slug: short string used in filenames, e.g. "20260624_1_comparison"

    Returns the absolute path to the rendered PNG, or None on failure.
    Requires Node.js and Puppeteer installed. No API keys required.
    """
    return _render_infographic(infographic_data, output_slug)


@mcp.tool()
def render_swatch_overlay(
    background_image_path: str,
    overlay_data: dict,
    output_slug: str,
) -> Optional[str]:
    """
    Composite a color-swatch label box and headline over a lifestyle photo background,
    then capture a 1080x1080 PNG. This is Stage 2 of the Trend Spotlight (swatch_overlay)
    format — call generate_ai_image first to produce the background_image_path.

    background_image_path: absolute path to the AI-generated lifestyle photo (PNG)
    overlay_data: dict with keys:
        "color_hex"     (str) — CSS hex color for the swatch square, e.g. "#C4926A"
        "color_name"    (str) — human-readable color name, e.g. "Terracotta Clay"
        "color_ref"     (str) — MAK-SHANG reference code, e.g. "MS-TC-04" (or "" to omit)
        "headline"      (str) — 2-5 word headline, rendered uppercase
        "footer_handle" (str) — Instagram handle, e.g. "@makshangpaints"
    output_slug: short string used in filenames, e.g. "20260625_1_trend-spotlight"

    Returns the absolute path to the rendered PNG, or None on failure.
    Requires Node.js and Puppeteer installed. No API keys required.
    """
    return _render_swatch_overlay(background_image_path, overlay_data, output_slug)


@mcp.tool()
def render_swatch_grid(
    swatch_data: dict,
    output_slug: str,
) -> Optional[str]:
    """
    Render a color-swatch comparison card (Format B) as a 1080x1080 PNG.
    Pure HTML/CSS layout — no AI image generation needed. Used for the Comparison archetype.

    swatch_data must match the swatch_grid schema:
        {
            "format":     "swatch_grid",
            "title_main": "Short punchy title (2–4 words)",
            "title_span": "accent word shown in red",
            "subtitle":   "One sentence — max 12 words",
            "badge":      "🎨 FINISH GUIDE",
            "date_label": "MAK-SHANG 2026",
            "source":     "Source: MAK-SHANG Paints | @makshangpaints",
            "swatches":   [
                {"color_hex": "#E02020", "label": "High-Gloss", "sublabel": "Sheen: 60–80%"},
                ...
            ],
            "footnote":   "Optional short note (omit or empty string to hide)"
        }
        Use 3–5 swatches. sublabel can include sheen %, finish type, or brief note.

    output_slug: short string for filenames, e.g. "20260625_3_comparison"

    Returns the absolute path to the rendered PNG, or None on failure.
    Requires Node.js and Puppeteer installed. No API keys required.
    """
    return _render_swatch_grid(swatch_data, output_slug)


@mcp.tool()
def render_before_after(
    after_image_path: str,
    before_after_data: dict,
    output_slug: str,
) -> Optional[str]:
    """
    Build a split-panel before/after card from a single AI-generated "after" image,
    then capture a 1080x1080 PNG. The "before" panel is the same image with a CSS
    desaturation/darkening filter — no second Gemini call required.
    Used for Local Adaptation and (optionally) Myth Buster archetypes.

    after_image_path: absolute path to the AI-generated "after" lifestyle photo (PNG)
    before_after_data: dict with keys:
        "headline"        (str) — optional 2–6 word headline shown in a top bar.
                                   Omit or "" for panels-only layout.
        "headline_accent" (str) — optional word within the headline to render in red italic.
                                   Ignored when headline is empty.
        "footer_handle"   (str) — Instagram handle, e.g. "@makshangpaints"
        "footer_tagline"  (str) — short tagline, e.g. "MAK-SHANG Paints · Ukhrul"
    output_slug: short string for filenames, e.g. "20260625_2_local-adaptation"

    Returns the absolute path to the rendered PNG, or None on failure.
    Requires Node.js and Puppeteer installed. No API keys required.
    """
    return _render_before_after(after_image_path, before_after_data, output_slug)


@mcp.tool()
def upload_to_github(
    local_path: str,
    remote_filename: Optional[str] = None,
) -> Optional[str]:
    """
    Upload a local image file to the mak-shang GitHub Pages repo via the GitHub Contents API.
    The public URL returned here is required before any Meta API publish call.

    local_path:       absolute path to the local PNG file
    remote_filename:  filename to use in the repo (defaults to the file's basename)

    Returns the public GitHub Pages URL on success, e.g.:
        https://xhangreichris-max.github.io/mak-shang/assets/posts/image_20260624_1.png
    Returns None on failure.

    Reads from environment:
        GITHUB_TOKEN       (required)
        GITHUB_REPO        (default: xhangreichris-max/mak-shang)
        GITHUB_POSTS_PATH  (default: assets/posts)
    """
    return _upload_to_github(local_path, remote_filename)


@mcp.tool()
def post_to_instagram(
    image_url: str,
    caption: str,
    dry_run: bool = False,
) -> Optional[str]:
    """
    Publish a single image post to the MAK-SHANG Instagram Business account.
    Uses the 2-step Meta Graph API flow: create media container, then publish.
    Does NOT auto-cross-post to Facebook — call post_to_facebook separately.

    image_url:  publicly accessible URL (must already be live on GitHub Pages)
    caption:    full post text with hashtags appended,
                format: "{caption_body}\n.\n.\n.\n{hashtags}"
    dry_run:    if True, logs intent without making API calls (default: False)

    Returns the Instagram media ID string on success, None on failure.

    Reads from environment:
        META_USER_ACCESS_TOKEN  (required, 60-day expiry)
        META_IG_USER_ID         (default: 17841421839438768)
    """
    return _post_to_instagram(image_url, caption, dry_run)


@mcp.tool()
def post_to_facebook(
    image_url: str,
    caption: str,
    dry_run: bool = False,
) -> Optional[str]:
    """
    Publish a single image post to the MAK-SHANG Facebook Page.
    Uses 1-step Meta Graph API: POST to /{page-id}/photos.
    Must use the Page Access Token — NOT the User Access Token.

    image_url:  publicly accessible URL (must already be live on GitHub Pages)
    caption:    full post text with hashtags appended,
                format: "{caption_body}\n.\n.\n.\n{hashtags}"
    dry_run:    if True, logs intent without making API calls (default: False)

    Returns the Facebook photo ID string on success, None on failure.

    Reads from environment:
        META_PAGE_ACCESS_TOKEN  (required, 60-day expiry)
        META_PAGE_ID            (default: 1139870945879021)
    """
    return _post_to_facebook(image_url, caption, dry_run)


if __name__ == "__main__":
    mcp.run()
