#!/usr/bin/env python3
"""
Tool: post_to_instagram

Publishes a single image post to the MAK-SHANG Instagram Business account.
Uses the 2-step Meta Graph API flow: create media container, then publish.

Primary function:
    post_to_instagram(image_url: str, caption: str, dry_run: bool = False) -> str | None

    image_url:  publicly accessible URL of the image (must be live on GitHub Pages)
    caption:    full post text with hashtags appended (format: "{caption}\n.\n.\n.\n{hashtags}")
    dry_run:    if True, logs intent without making API calls

    Returns the Instagram media ID string on success, None on failure.

    Reads META_IG_USER_ID and META_USER_ACCESS_TOKEN from .env.
    NOTE: IG publish does NOT auto-cross-post to Facebook — post_to_facebook must be called separately.
"""

import sys, os, json, time
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


def post_to_instagram(image_url, caption, dry_run=False):
    """
    Publish a photo to Instagram via the 2-step Media Container flow.
    Returns the published media ID, or None on failure.
    """
    env = _load_env()
    ig_id = env.get("META_IG_USER_ID", "")
    token = env.get("META_USER_ACCESS_TOKEN", "")

    if not ig_id or not token:
        print("ERROR: META_IG_USER_ID or META_USER_ACCESS_TOKEN not set in .env")
        return None

    if dry_run:
        print(f"[DRY RUN] Would create IG container for: {image_url[:70]}")
        print(f"[DRY RUN] Would publish to IG account {ig_id}")
        return "dry_run_ig_id"

    print("  Creating IG media container...")
    try:
        resp = _graph_post(
            f"{GRAPH}/{ig_id}/media",
            {"image_url": image_url, "caption": caption, "access_token": token},
        )
    except RuntimeError as e:
        print(f"  IG container creation failed: {e}")
        return None

    container_id = resp.get("id")
    if not container_id:
        print(f"  IG container creation returned no ID: {resp}")
        return None
    print(f"  Container created: {container_id}")

    time.sleep(3)

    print("  Publishing IG container...")
    try:
        resp = _graph_post(
            f"{GRAPH}/{ig_id}/media_publish",
            {"creation_id": container_id, "access_token": token},
        )
    except RuntimeError as e:
        print(f"  IG publish failed: {e}")
        return None

    media_id = resp.get("id")
    if media_id:
        print(f"  Instagram published: media_id={media_id}")
    else:
        print(f"  IG publish returned no ID: {resp}")
    return media_id


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    if len(args) < 2:
        print('usage: python tools/post_to_instagram.py "<image_url>" "<caption>" [--dry-run]')
        sys.exit(1)
    result = post_to_instagram(args[0], args[1], dry_run=dry)
    sys.exit(0 if result else 1)
