#!/usr/bin/env python3
"""
tools/run_queue.py

Reads queue.json, finds the next unposted slot, and publishes it:
  1. queue_images/img_XX.png (text/branding already baked in — no rendering here)
  2. Upload to GitHub Pages via upload_to_github()
  3. Publish to Instagram via post_to_instagram()
  4. Publish to Facebook via post_to_facebook()
  5. Mark that slot posted=true in queue.json and commit+push the change

Usage:
    python tools/run_queue.py

Meta publish failures are warnings, not hard errors — if both Instagram and
Facebook fail, the slot is left posted=false so the next scheduled run retries it.
"""

import json, os, sys, time, subprocess
import urllib.request, ssl

PIPELINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(PIPELINE_DIR, "tools")
sys.path.insert(0, TOOLS_DIR)

from upload_to_github import upload_to_github
from post_to_instagram import post_to_instagram
from post_to_facebook import post_to_facebook

QUEUE_PATH = os.path.join(PIPELINE_DIR, "queue.json")
QUEUE_IMAGES_DIR = os.path.join(PIPELINE_DIR, "queue_images")

_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE


def _load_queue():
    with open(QUEUE_PATH, encoding="utf-8") as f:
        return json.load(f)


def _save_queue(posts):
    with open(QUEUE_PATH, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)


def _next_unposted(posts):
    pending = [p for p in posts if not p.get("posted")]
    if not pending:
        return None
    return min(pending, key=lambda p: p["slot"])


def _wait_for_url(url, timeout=180, interval=10):
    """Poll a URL until it returns HTTP 200 or timeout expires.

    GitHub Pages typically takes 60-120s to deploy after a commit.
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
                    print(f"  Image live after ~{attempt * interval}s")
                    return True
        except Exception:
            pass
        remaining = int(deadline - time.time())
        print(f"  Not ready yet (attempt {attempt}, ~{remaining}s remaining)...")
        time.sleep(interval)
    print(f"  WARNING: image URL not available after {timeout}s — posting anyway")
    return False


def _commit_queue(slot):
    try:
        subprocess.run(["git", "add", "queue.json"], cwd=PIPELINE_DIR, check=True)
        staged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=PIPELINE_DIR)
        if staged.returncode == 0:
            print("  No changes to commit")
            return
        subprocess.run(
            ["git", "commit", "-m", f"chore: slot {slot} posted [skip ci]"],
            cwd=PIPELINE_DIR, check=True,
        )
        subprocess.run(["git", "push"], cwd=PIPELINE_DIR, check=True)
        print("  Committed and pushed queue.json")
    except subprocess.CalledProcessError as e:
        print(f"  WARNING: git commit/push failed: {e}")


def run_queue():
    posts = _load_queue()
    post = _next_unposted(posts)
    if post is None:
        print("Queue empty — every slot already posted. Nothing to do.")
        sys.exit(0)

    slot = post["slot"]
    print(f"\n=== Queue slot {slot} | type={post.get('type')} ===")

    image_path = os.path.join(QUEUE_IMAGES_DIR, f"img_{slot:02d}.png")
    if not os.path.exists(image_path):
        print(f"ERROR: image not found for slot {slot}: {image_path}")
        sys.exit(1)

    # --- Upload to GitHub Pages ---
    print("\n[upload]")
    public_url = upload_to_github(image_path)
    if not public_url:
        print(f"ERROR: GitHub upload failed for slot {slot}")
        sys.exit(1)

    _wait_for_url(public_url)

    # --- Publish ---
    full_caption = f"{post['caption']}\n.\n.\n.\n{post['hashtags']}"

    print("\n[instagram]")
    ig_id = post_to_instagram(public_url, full_caption)
    if not ig_id:
        print(f"WARNING: Instagram publish failed for slot {slot}")

    print("\n[facebook]")
    fb_id = post_to_facebook(public_url, full_caption)
    if not fb_id:
        print(f"WARNING: Facebook publish failed for slot {slot}")

    # Partial success (one platform) still counts as posted, matching run_slot.py's convention.
    meta_ok = bool(ig_id or fb_id)
    post["publish_result"] = {"instagram": ig_id, "facebook": fb_id}
    post["posted"] = meta_ok
    if not meta_ok:
        print(f"WARNING: both Instagram and Facebook failed for slot {slot} — will retry next run")

    _save_queue(posts)

    print("\n[commit]")
    _commit_queue(slot)

    print(f"\nSlot {slot} done — Instagram: {ig_id} | Facebook: {fb_id}")


if __name__ == "__main__":
    run_queue()
