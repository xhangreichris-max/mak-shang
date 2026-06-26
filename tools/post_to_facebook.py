#!/usr/bin/env python3
"""
Tool: post_to_facebook

Publishes a single image post to the MAK-SHANG Facebook Page.
Uses the 1-step Meta Graph API: POST to /{page-id}/photos with Page Access Token.

Primary function:
    post_to_facebook(image_url: str, caption: str, dry_run: bool = False) -> str | None

    image_url:  publicly accessible URL of the image (must be live on GitHub Pages)
    caption:    full post text with hashtags appended (format: "{caption}\n.\n.\n.\n{hashtags}")
    dry_run:    if True, logs intent without making API calls

    Returns the Facebook photo ID string on success, None on failure.

    IMPORTANT: Uses the Page Access Token (META_PAGE_ACCESS_TOKEN), NOT the User Access Token.
    Reads META_PAGE_ID and META_PAGE_ACCESS_TOKEN from .env.
"""

import sys, os, json
import urllib.request, urllib.parse, urllib.error, ssl

PIPELINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRAPH = "https://graph.facebook.com/v21.0"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def _load_env():
    env = dict(os.environ)  # process env first so MCP-injected vars are always available
    env_path = os.path.join(PIPELINE_DIR, ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def _graph_post(url, params):
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")
        raise RuntimeError(f"HTTP {e.code}: {body[:400]}")


def post_to_facebook(image_url, caption, dry_run=False):
    """
    Post a photo to the MAK-SHANG Facebook Page.
    Returns the photo ID, or None on failure.
    """
    env = _load_env()
    page_id = env.get("META_PAGE_ID", "")
    token = env.get("META_PAGE_ACCESS_TOKEN", "")

    if not page_id or not token:
        print("ERROR: META_PAGE_ID or META_PAGE_ACCESS_TOKEN not set in .env")
        return None

    if dry_run:
        print(f"[DRY RUN] Would POST photo to FB page {page_id}: {image_url[:70]}")
        return "dry_run_fb_id"

    print("  Posting to Facebook Page...")
    try:
        resp = _graph_post(
            f"{GRAPH}/{page_id}/photos",
            {"url": image_url, "caption": caption, "access_token": token},
        )
    except RuntimeError as e:
        print(f"  FB post failed: {e}")
        return None

    photo_id = resp.get("id") or resp.get("post_id")
    if photo_id:
        print(f"  Facebook published: id={photo_id}")
    else:
        print(f"  FB post returned no ID: {resp}")
    return photo_id


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    if len(args) < 2:
        print('usage: python tools/post_to_facebook.py "<image_url>" "<caption>" [--dry-run]')
        sys.exit(1)
    result = post_to_facebook(args[0], args[1], dry_run=dry)
    sys.exit(0 if result else 1)
