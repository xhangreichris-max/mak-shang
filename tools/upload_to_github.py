#!/usr/bin/env python3
"""
Tool: upload_to_github

Uploads a local image file to the mak-shang GitHub Pages repo via the GitHub Contents API.
Returns the public GitHub Pages URL, which is required before any Meta API post.

Primary function:
    upload_to_github(local_path: str, remote_filename: str = None) -> str | None

    local_path:       absolute path to the local PNG file
    remote_filename:  filename to use in the repo (defaults to os.path.basename(local_path))

    Returns the public GitHub Pages URL, e.g.:
        https://xhangreichris-max.github.io/mak-shang/assets/posts/image_20260624_1.png
    Returns None on failure.

    Reads GITHUB_TOKEN, GITHUB_REPO, GITHUB_POSTS_PATH from .env.
"""

import sys, os, json, base64, datetime
import urllib.request, urllib.error, ssl

PIPELINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

GITHUB_API = "https://api.github.com"


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


def _get_existing_sha(repo, path, token):
    url = f"{GITHUB_API}/repos/{repo}/contents/{path}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
            return json.loads(r.read().decode("utf-8")).get("sha")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def upload_to_github(local_path, remote_filename=None):
    """
    Upload a local image to GitHub Pages and return its public URL.
    Returns None on failure.
    """
    env = _load_env()
    token = env.get("GITHUB_TOKEN", "")
    repo = env.get("GITHUB_REPO", "xhangreichris-max/mak-shang")
    posts_path = env.get("GITHUB_POSTS_PATH", "assets/posts")

    if not token:
        print("ERROR: GITHUB_TOKEN not set in .env")
        return None

    if not os.path.exists(local_path):
        print(f"ERROR: file not found: {local_path}")
        return None

    if not remote_filename:
        remote_filename = os.path.basename(local_path)

    repo_file_path = f"{posts_path}/{remote_filename}"

    with open(local_path, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode("utf-8")

    existing_sha = _get_existing_sha(repo, repo_file_path, token)
    today = datetime.date.today().isoformat()
    payload = {
        "message": f"Add post image {remote_filename} [{today}]",
        "content": content_b64,
    }
    if existing_sha:
        payload["sha"] = existing_sha

    url = f"{GITHUB_API}/repos/{repo}/contents/{repo_file_path}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="PUT",
    )

    try:
        with urllib.request.urlopen(req, context=ctx, timeout=60) as r:
            json.loads(r.read().decode("utf-8"))
        owner, repo_name = repo.split("/", 1)
        public_url = f"https://{owner}.github.io/{repo_name}/{repo_file_path}"
        print(f"  Uploaded: {public_url}")
        return public_url
    except urllib.error.HTTPError as e:
        print(f"  GitHub upload error {e.code}: {e.read().decode('utf-8', 'ignore')[:300]}")
        return None
    except Exception as e:
        print(f"  GitHub upload error: {e}")
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python tools/upload_to_github.py <local_image> [remote_filename]")
        sys.exit(1)
    local = sys.argv[1]
    remote = sys.argv[2] if len(sys.argv) > 2 else None
    url = upload_to_github(local, remote)
    print(url if url else "FAILED")
    sys.exit(0 if url else 1)
