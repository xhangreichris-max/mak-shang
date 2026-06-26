#!/usr/bin/env python3
"""
tools/run_reasoning.py

Daily reasoning orchestrator for MAK-SHANG Paints.

Performs Steps 1–8 of the daily workflow using the Gemini API:
  1. Clears content_today.json with in_progress sentinel (stale-state guard)
  2. Calls read_rotation_log → due_archetypes
  3. Calls fetch_trends → fresh candidates (hard stop on RuntimeError)
  4. Sends all data + agent-instructions.md to Gemini (JSON mode)
  5. Validates the response against the expected schema
  6. Writes content_today.json with "published": false on every post

Usage:
    python tools/run_reasoning.py

Reads credentials from environment variables (GitHub Actions) or .env file (local).
Required: GEMINI_API_KEY
Optional: BRAVE_SEARCH_API_KEY (RSS-only mode without it)
"""

import json, os, sys, datetime, ssl
import urllib.request, urllib.error

PIPELINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(PIPELINE_DIR, "tools")
sys.path.insert(0, TOOLS_DIR)

from read_rotation_log import read_rotation_log
from fetch_trends import fetch_trends

AGENT_INSTRUCTIONS_PATH = os.path.join(PIPELINE_DIR, "agent-instructions.md")
CONTENT_TODAY_PATH = os.path.join(PIPELINE_DIR, "content_today.json")

REASONING_MODEL_PRIMARY = "gemini-2.5-pro"
REASONING_MODEL_FALLBACK = "gemini-2.5-flash"
GEMINI_GENERATE_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
)

VALID_ARCHETYPES = {
    "Trend Spotlight", "Myth Buster", "Cost & Care Guide",
    "Before You Paint", "Local Adaptation", "Comparison",
}
VALID_FORMATS = {"swatch_overlay", "ai_image", "before_after", "infographic", "swatch_grid"}
REQUIRED_BASE_FIELDS = [
    "slot", "published", "archetype", "output_format",
    "source_title", "source_url", "date", "caption", "hashtags",
]

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def _load_env():
    env = dict(os.environ)
    env_path = os.path.join(PIPELINE_DIR, ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def _write_sentinel(today):
    sentinel = {"status": "in_progress", "date": today, "posts": []}
    with open(CONTENT_TODAY_PATH, "w", encoding="utf-8") as f:
        json.dump(sentinel, f, indent=2)
    print(f"Sentinel written to content_today.json (date: {today})")


def _build_prompt(agent_instructions, due_archetypes, candidates, topic_log, today):
    candidates = candidates[:15]
    recent_topics = topic_log[-30:] if len(topic_log) > 30 else topic_log
    return f"""You are performing a one-shot daily content generation task for MAK-SHANG Paints.
Follow every rule in the AGENT INSTRUCTIONS below exactly.
Output ONLY a valid JSON array — no explanation, no markdown, no code fences, just raw JSON.

=== AGENT INSTRUCTIONS ===
{agent_instructions}

=== TODAY'S DATA ===
Date: {today}
Due archetypes (fill exactly these 3 slots, one per post, no repeats):
{json.dumps(due_archetypes)}

Trend candidates (use these to inform post topics and image prompts; score and pick best):
{json.dumps(candidates, indent=2, ensure_ascii=False)}

Recently covered topics (avoid repeating these — 14-day dedup window):
{json.dumps(recent_topics, indent=2, ensure_ascii=False)}

=== REQUIRED OUTPUT FORMAT ===
A JSON array of exactly 3 post objects. Required fields on EVERY object:
  "slot"          : integer 1, 2, or 3 (publication order)
  "published"     : false  (never true — publishing is handled by a separate script)
  "archetype"     : one of the 6 archetype names exactly as listed in the instructions
  "output_format" : "swatch_overlay" | "ai_image" | "before_after" | "infographic" | "swatch_grid"
  "source_title"  : the candidate article title this post draws from
  "source_url"    : the candidate URL
  "date"          : "{today}"
  "caption"       : full caption text, 100–180 words, no hashtags, no em-dashes
  "hashtags"      : full hashtag string (single string, no internal newlines)

Additional fields required by output_format:
  "swatch_overlay" → add "image_prompt" (str, ≤120 words) and "overlay_data" (object)
  "ai_image"       → add "image_prompt" (str, ≤120 words)
  "before_after"   → add "image_prompt" (str, ≤120 words) and "before_after_data" (object)
  "infographic"    → add "infographic_data" (object — ranked_bars or hero_number schema)
  "swatch_grid"    → add "infographic_data" (object — swatch_grid schema)

Do NOT include "rendered_png", "public_image_url", or "publish_result" — added by publishing step.
Output ONLY the JSON array. No surrounding text. No markdown. No code fences.
"""


def _call_gemini(prompt, api_key, model):
    url = GEMINI_GENERATE_URL.format(model=model, key=api_key)
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 1.0,
            "maxOutputTokens": 8192,
        },
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=180) as r:
            data = json.loads(r.read().decode("utf-8"))
        candidates_list = data.get("candidates", [])
        if not candidates_list:
            print(f"  {model}: empty candidates list in response")
            return None
        text = (
            candidates_list[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )
        return text.strip() or None
    except urllib.error.HTTPError as e:
        print(f"  {model}: HTTP {e.code} — {e.read().decode('utf-8', 'ignore')[:300]}")
        return None
    except Exception as e:
        print(f"  {model}: {e}")
        return None


def _strip_fences(text):
    text = text.strip()
    if text.startswith("```"):
        # Remove opening fence (```json or just ```)
        first_newline = text.find("\n")
        text = text[first_newline + 1:] if first_newline != -1 else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def _validate_post(post, expected_slot, today):
    errors = []
    for field in REQUIRED_BASE_FIELDS:
        if field not in post:
            errors.append(f"missing '{field}'")

    if not errors:
        if post.get("slot") != expected_slot:
            errors.append(f"slot={post.get('slot')} expected {expected_slot}")
        if post.get("published") is not False:
            errors.append("'published' must be false")
        if post.get("archetype") not in VALID_ARCHETYPES:
            errors.append(f"invalid archetype: {post.get('archetype')!r}")
        if post.get("output_format") not in VALID_FORMATS:
            errors.append(f"invalid output_format: {post.get('output_format')!r}")
        if post.get("date") != today:
            errors.append(f"date={post.get('date')!r} expected {today!r}")

        fmt = post.get("output_format", "")
        if fmt in ("swatch_overlay", "ai_image", "before_after"):
            if not post.get("image_prompt"):
                errors.append("missing 'image_prompt'")
        if fmt == "swatch_overlay" and not post.get("overlay_data"):
            errors.append("missing 'overlay_data'")
        if fmt == "before_after" and not post.get("before_after_data"):
            errors.append("missing 'before_after_data'")
        if fmt in ("infographic", "swatch_grid") and not post.get("infographic_data"):
            errors.append("missing 'infographic_data'")

    return errors


def _validate_posts(posts, today, due_archetypes):
    if not isinstance(posts, list) or len(posts) != 3:
        return [
            f"expected array of 3 posts, got {type(posts).__name__} "
            f"len={len(posts) if isinstance(posts, list) else '?'}"
        ]

    all_errors = []
    used_archetypes = set()

    for i, post in enumerate(posts):
        errs = _validate_post(post, i + 1, today)
        if errs:
            all_errors.append(f"Post {i+1}: {'; '.join(errs)}")
        arch = post.get("archetype")
        if arch in used_archetypes:
            all_errors.append(f"Post {i+1}: duplicate archetype '{arch}'")
        used_archetypes.add(arch)

    for arch in due_archetypes:
        if arch not in used_archetypes:
            all_errors.append(f"Due archetype '{arch}' not present in output")

    return all_errors


def run_reasoning():
    env = _load_env()
    api_key = env.get("GEMINI_API_KEY", "")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set in environment or .env")
        sys.exit(1)

    today = datetime.date.today().isoformat()

    # Step 1.5: overwrite any stale content_today.json with sentinel
    _write_sentinel(today)

    # Step 1: read rotation log
    print("\n=== Step 1: Reading rotation log ===")
    rotation = read_rotation_log()
    due_archetypes = rotation["due_archetypes"]
    topic_log = rotation["topic_log"]
    print(f"Due archetypes: {due_archetypes}")
    print(f"Topic log entries: {len(topic_log)}")

    # Step 2: fetch trend candidates (RuntimeError = hard stop)
    print("\n=== Step 2: Fetching trend candidates ===")
    try:
        candidates = fetch_trends()
    except RuntimeError as e:
        print(
            "\nDAILY RUN FAILED — fetch_trends could not find enough fresh candidates.\n"
            f"Reason: {e}\n"
            "No content has been generated or published today. "
            "Check fetch_trends_failed.json for diagnostics."
        )
        sys.exit(1)
    print(f"Using {min(len(candidates), 15)} of {len(candidates)} candidates for scoring")

    # Steps 3–8: send to Gemini for full reasoning
    print("\n=== Steps 3–8: Gemini reasoning ===")
    with open(AGENT_INSTRUCTIONS_PATH, encoding="utf-8") as f:
        agent_instructions = f.read()

    prompt = _build_prompt(agent_instructions, due_archetypes, candidates, topic_log, today)

    raw_json = None
    for model in (REASONING_MODEL_PRIMARY, REASONING_MODEL_FALLBACK):
        print(f"Calling {model} ...")
        raw_json = _call_gemini(prompt, api_key, model)
        if raw_json:
            print(f"  Response received ({len(raw_json):,} chars)")
            break
        print(f"  {model} failed, trying fallback ...")

    if not raw_json:
        print("ERROR: All Gemini models failed to return a response")
        sys.exit(1)

    # Parse JSON (strip accidental fences just in case)
    raw_json = _strip_fences(raw_json)
    try:
        posts = json.loads(raw_json)
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse Gemini response as JSON: {e}")
        print(f"Raw response (first 500 chars):\n{raw_json[:500]}")
        sys.exit(1)

    # Validate
    errors = _validate_posts(posts, today, due_archetypes)
    if errors:
        print("ERROR: Validation failed:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    # Write content_today.json
    with open(CONTENT_TODAY_PATH, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)

    print(f"\ncontent_today.json written — {len(posts)} posts:")
    for p in posts:
        print(f"  Slot {p['slot']}: {p['archetype']} ({p['output_format']})")


if __name__ == "__main__":
    run_reasoning()
