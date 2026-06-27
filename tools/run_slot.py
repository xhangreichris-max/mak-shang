#!/usr/bin/env python3
"""
tools/run_slot.py

Render, upload, and publish one post slot from content_today.json.

Usage:
    python tools/run_slot.py <slot>     (slot is 1, 2, or 3)

Safety checks (in order) before any action:
  1. Date guard    — post.date must equal today's date
  2. Slot guard    — a post with the requested slot number must exist
  3. Published guard — post.published must be false (skip silently if already true)

On success, updates content_today.json for this post:
  - post.published = true
  - post.rendered_png = local path to rendered PNG
  - post.public_image_url = GitHub Pages URL
  - post.publish_result = {"instagram": "<id>", "facebook": "<id>"}

If slot == 3, also calls write_rotation_log with all 3 posts after publishing.

Exits with code 0 on success (including the idempotent "already published" case).
Exits with code 1 on hard errors (stale date, render failure, upload failure).
Meta publish failures are warnings, not hard errors — the run still commits state.
"""

import json, os, sys, datetime, time, re, ssl
import urllib.request

PIPELINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(PIPELINE_DIR, "tools")
sys.path.insert(0, TOOLS_DIR)

from generate_ai_image import generate_ai_image
from render_infographic import render_infographic
from render_swatch_overlay import render_swatch_overlay
from render_swatch_grid import render_swatch_grid
from render_before_after import render_before_after
from upload_to_github import upload_to_github
from post_to_instagram import post_to_instagram
from post_to_facebook import post_to_facebook
from write_rotation_log import write_rotation_log

CONTENT_TODAY_PATH = os.path.join(PIPELINE_DIR, "content_today.json")
IMAGES_DIR = os.path.join(PIPELINE_DIR, "generated_images")

_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE


def _wait_for_url(url, timeout=180, interval=10):
    """Poll a URL until it returns HTTP 200 or timeout expires.

    GitHub Pages typically takes 60–120 s to deploy after a commit.
    Meta will reject the post if the image URL isn't live yet.
    """
    print(f"  Waiting for GitHub Pages to serve image (up to {timeout}s)...")
    deadline = time.time() + timeout
    attempt = 0
    while time.time() < deadline:
        attempt += 1
        try:
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req, context=_ssl_ctx, timeout=10) as r:
                if r.status == 200:
                    elapsed = attempt * interval
                    print(f"  Image live after ~{elapsed}s")
                    return True
        except Exception:
            pass
        remaining = int(deadline - time.time())
        print(f"  Not ready yet (attempt {attempt}, ~{remaining}s remaining) ...")
        time.sleep(interval)
    print(f"  WARNING: image URL not available after {timeout}s — posting anyway")
    return False


def _load_posts():
    with open(CONTENT_TODAY_PATH, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        status = data.get("status", "unknown")
        raise RuntimeError(
            f"content_today.json is in sentinel state ({status!r}) — "
            "run_reasoning.py has not completed successfully"
        )
    return data


def _save_posts(posts):
    with open(CONTENT_TODAY_PATH, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)


def _archetype_slug(archetype):
    # "Cost & Care Guide" → "cost-and-care-guide", "Before You Paint" → "before-you-paint"
    slug = archetype.lower()
    slug = re.sub(r"[&]", "and", slug)
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def _output_slug(post):
    date_str = post["date"].replace("-", "")
    slot = post["slot"]
    slug = _archetype_slug(post["archetype"])
    return f"{date_str}_{slot}_{slug}"


def _image_output_path(post):
    os.makedirs(IMAGES_DIR, exist_ok=True)
    slug = _output_slug(post)
    return os.path.join(IMAGES_DIR, f"image_{slug}.png")


def _render(post):
    fmt = post["output_format"]
    slug = _output_slug(post)
    os.makedirs(IMAGES_DIR, exist_ok=True)

    if fmt == "ai_image":
        img_path = _image_output_path(post)
        ok = generate_ai_image(post["image_prompt"], img_path)
        return img_path if ok else None

    elif fmt == "swatch_overlay":
        img_path = _image_output_path(post)
        ok = generate_ai_image(post["image_prompt"], img_path)
        if not ok:
            return None
        time.sleep(2)  # Gemini rate limit
        return render_swatch_overlay(img_path, post["overlay_data"], slug)

    elif fmt == "before_after":
        img_path = _image_output_path(post)
        ok = generate_ai_image(post["image_prompt"], img_path)
        if not ok:
            return None
        time.sleep(2)
        return render_before_after(img_path, post["before_after_data"], slug)

    elif fmt == "infographic":
        return render_infographic(post["infographic_data"], slug)

    elif fmt == "swatch_grid":
        return render_swatch_grid(post["infographic_data"], slug)

    else:
        print(f"ERROR: unknown output_format '{fmt}'")
        return None


def run_slot(slot_num):
    today = datetime.date.today().isoformat()
    print(f"\n=== Slot {slot_num} | {today} ===")

    # Load posts
    try:
        posts = _load_posts()
    except FileNotFoundError:
        print("ERROR: content_today.json not found")
        sys.exit(1)
    except (json.JSONDecodeError, RuntimeError) as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Slot guard
    post = next((p for p in posts if p.get("slot") == slot_num), None)
    if post is None:
        print(f"ERROR: no post with slot={slot_num} in content_today.json")
        sys.exit(1)

    # Date guard
    post_date = post.get("date", "")
    if post_date != today:
        print(
            f"ERROR: stale content — post.date={post_date!r} but today is {today!r}. "
            "Run morning task first to regenerate content_today.json."
        )
        sys.exit(1)

    # Published guard (idempotent — not an error)
    if post.get("published") is True:
        print(f"Slot {slot_num} already published — nothing to do")
        sys.exit(0)

    print(f"Processing: {post['archetype']} ({post['output_format']})")

    # --- Render ---
    print("\n[render]")
    rendered_png = _render(post)
    if not rendered_png:
        print(f"ERROR: render failed for slot {slot_num} ({post['output_format']})")
        sys.exit(1)
    post["rendered_png"] = rendered_png
    print(f"Rendered: {rendered_png}")

    # --- Upload to GitHub Pages ---
    print("\n[upload]")
    time.sleep(1)
    public_url = upload_to_github(rendered_png)
    if not public_url:
        print(f"ERROR: GitHub upload failed for slot {slot_num}")
        sys.exit(1)
    post["public_image_url"] = public_url

    # Poll until GitHub Pages serves the image — Meta will reject it if the CDN hasn't deployed yet
    _wait_for_url(public_url)

    # --- Publish to Instagram ---
    print("\n[instagram]")
    full_caption = f"{post['caption']}\n.\n.\n.\n{post['hashtags']}"
    ig_id = post_to_instagram(public_url, full_caption)
    if not ig_id:
        print(f"WARNING: Instagram publish failed for slot {slot_num}")

    # --- Publish to Facebook ---
    print("\n[facebook]")
    fb_id = post_to_facebook(public_url, full_caption)
    if not fb_id:
        print(f"WARNING: Facebook publish failed for slot {slot_num}")

    # Update post state
    post["publish_result"] = {"instagram": ig_id, "facebook": fb_id}
    post["published"] = True

    # Persist updated content_today.json
    _save_posts(posts)
    print(f"\nSlot {slot_num} done — Instagram: {ig_id} | Facebook: {fb_id}")

    # Slot 3: write rotation logs
    if slot_num == 3:
        print("\n[rotation log]")
        ok = write_rotation_log(posts)
        if not ok:
            print("WARNING: write_rotation_log failed")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python tools/run_slot.py <slot>    (1, 2, or 3)")
        sys.exit(1)
    try:
        slot = int(sys.argv[1])
    except ValueError:
        print(f"ERROR: slot must be an integer, got {sys.argv[1]!r}")
        sys.exit(1)
    if slot not in (1, 2, 3):
        print(f"ERROR: slot must be 1, 2, or 3 — got {slot}")
        sys.exit(1)
    run_slot(slot)
