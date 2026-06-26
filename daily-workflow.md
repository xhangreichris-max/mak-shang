# MAK-SHANG Daily Workflow

This document defines the step sequence for the MAK-SHANG Paints daily content run. Paste this (or reference it) as the task definition for an Antigravity scheduled agent.

For all reasoning steps, follow the detailed criteria in [agent-instructions.md](agent-instructions.md).

---

## Overview

Each day the agent produces 3 posts (one per archetype slot) and publishes them to Instagram and Facebook. The run has two phases:

- **Reasoning phase** (steps 1–8): the agent reads data, thinks, and writes content
- **Execution phase** (steps 9–13): tool calls that render, upload, and publish

---

## Step sequence

### Step 1 — Read rotation state
**Tool:** `tools/read_rotation_log.read_rotation_log()`

Returns `{due_archetypes, archetype_log, topic_log}`.
Record `due_archetypes` — these are the 3 archetype slots to fill today.

---

### Step 1.5 — Clear stale state (9 AM task only)
Before calling any tools, delete or overwrite `content_today.json` with the following
sentinel so no stale data can be accidentally used if the run fails partway through:

```json
{"status": "in_progress", "date": "YYYY-MM-DD", "posts": []}
```

This must happen before Step 2. The 1 PM and 7 PM tasks skip this step.

---

### Step 2 — Fetch trend candidates
**Tool:** `tools/fetch_trends.fetch_trends()`

Returns a list of fresh candidates and writes `trend_candidates.json`.
Cap at 15 candidates for scoring.

**HARD STOP — if `fetch_trends` raises a `RuntimeError` (prefixed `ABORT:`):**
- Do NOT write or update `content_today.json`
- Do NOT render, generate, upload, or publish anything
- Report the exact error message from the exception
- Check `fetch_trends_failed.json` in the pipeline directory for diagnostics
- The existing `content_today.json` (if any) is stale — do NOT treat it as valid for today

The daily run must not proceed past Step 2 without at least 3 fresh candidates.

---

### Step 3 — Score and select [AGENT REASONING]
See **Steps 3 and 4** in [agent-instructions.md](agent-instructions.md).

- Score each candidate on 4 dimensions (Recency, Visual Appeal, Local Relevance, Practicality), each 1–5
- Rank by total score
- Assign one archetype per post from `due_archetypes`, no repeats
- Set `output_format` per archetype (see archetype table in agent-instructions.md)

Output: 3 post objects with `archetype`, `output_format`, `source_title`, `source_url`, `date`

---

### Step 4 — Write captions [AGENT REASONING]
See **Step 5** in [agent-instructions.md](agent-instructions.md).

- One caption per post, 100–180 words
- No hashtags in caption body, no em-dashes, no banned filler words
- Ends with a save/share CTA
- Same caption text is used for both Instagram and Facebook

Output: adds `caption` and `hashtags` to each post object

---

### Step 5 — Write image prompts [AGENT REASONING — ai_image posts only]
See **Step 6** in [agent-instructions.md](agent-instructions.md).

- One image prompt per `ai_image` post, under 120 words
- Describes an original scene in Manipur/NE India, brand palette, Tangkhul warmth
- Brand directive is appended automatically by the tool — do not repeat it

Output: adds `image_prompt` to each `ai_image` post object

---

### Step 6 — Generate infographic data [AGENT REASONING — infographic posts only]
See **Step 7** in [agent-instructions.md](agent-instructions.md).

- Comparison / Cost & Care Guide → `ranked_bars` schema (3–5 bars with % values)
- Before You Paint → `hero_number` schema (exactly 5 checklist items)
- Use plausible data relevant to Indian home painting; cite MAK-SHANG as source

Output: adds `infographic_data` to each `infographic` post object

---

### Step 7 — Write content_today.json [AGENT]
See **Step 8** in [agent-instructions.md](agent-instructions.md).

Write the completed 3-post array to `content_today.json` in the pipeline directory.
Run the quality checklist at the bottom of agent-instructions.md before writing.

Every post object **must** include `"slot"` (1, 2, or 3 in publication order) and `"published": false`.
These fields enable the separate 1 PM and 7 PM publish tasks to target only their own post and
to skip re-publishing on retry. Each publish task writes `"published": true` back to the file after
it succeeds; do not set `"published": true` here.

---

### Step 8 — Render infographics
**Tool:** `tools/render_infographic.render_infographic(infographic_data, output_slug)`

Call once per `infographic` post.

`output_slug` format: `{YYYYMMDD}_{post_index}_{archetype_slug}`
Examples:
- Post 1 (Comparison): `20260624_1_comparison`
- Post 2 (Cost & Care Guide): `20260624_2_cost-and-care-guide`
- Post 3 (Before You Paint): `20260624_3_before-you-paint`

Returns the local path to the PNG, or `None` on failure.
Store the path as `rendered_png` on the post object. If `None`, skip this post's upload and publish steps.

---

### Step 9 — Generate AI lifestyle images
**Tool:** `tools/generate_ai_image.generate_ai_image(prompt, output_path)`

Call once per `ai_image` post.

`output_path` format: `{PIPELINE_DIR}/image_{YYYYMMDD}_{post_index}_{archetype_slug}.png`

Returns `True` (saved) or `False` (failed).
Store the path as `rendered_png` on the post object if `True`. If `False`, skip upload and publish for this post.

**Wait 2 seconds between calls** to respect Gemini rate limits.

---

### Step 10 — Upload images to GitHub Pages
**Tool:** `tools/upload_to_github.upload_to_github(local_path)`

Call once per post that has a valid `rendered_png` path.

Returns the public GitHub Pages URL, or `None` on failure.
Store as `public_image_url` on the post object. If `None`, skip publish for this post.

**Wait 1 second between calls.**

---

### Step 11 — Publish to Instagram
**Tool:** `tools/post_to_instagram.post_to_instagram(image_url, full_caption)`

Call once per post that has a valid `public_image_url`.

`full_caption` = `{post["caption"]}\n.\n.\n.\n{post["hashtags"]}`

Returns the Instagram media ID or `None`.
Store as `publish_result.instagram` on the post object.

**Wait 5 seconds between posts** to respect Meta rate limits.

---

### Step 12 — Publish to Facebook
**Tool:** `tools/post_to_facebook.post_to_facebook(image_url, full_caption)`

Call once per post that has a valid `public_image_url` (same image, same caption as Instagram).

Returns the Facebook photo ID or `None`.
Store as `publish_result.facebook` on the post object.

**Wait 5 seconds between posts.**

---

### Step 13 — Update rotation logs
**Tool:** `tools/write_rotation_log.write_rotation_log(posts)`

Call once at the very end, passing the full list of post objects.
Each post **must** include all of the following fields — omitting any will leave the published archive incomplete and trigger a WARNING in the tool output:

| Field | Set in step | Example |
|---|---|---|
| `archetype` | Step 3 | `"Before You Paint"` |
| `output_format` | Step 3 | `"infographic"` |
| `source_title` | Step 3 | `"Can You Paint Indoors During Monsoon?"` |
| `source_url` | Step 3 | `"https://..."` |
| `date` | Step 3 | `"2026-06-26"` |
| `caption` | Step 4 | full caption string |
| `hashtags` | Step 4 | hashtag string |
| `rendered_png` | Step 8 or 9 | local file path |
| `public_image_url` | Step 10 | GitHub Pages URL |
| `publish_result` | Steps 11–12 | `{"instagram": "...", "facebook": "..."}` |

This prevents the same archetypes and topics from repeating in the next 14 days, and ensures each day's published archive is fully self-contained.

---

## Data flow summary

```
read_rotation_log()     → due_archetypes (3 archetype slot names)
fetch_trends()          → candidates list (up to 15)
                               ↓
[AGENT] score + select + assign archetypes
[AGENT] write captions, hashtags
[AGENT] write image_prompt or infographic_data per post
[AGENT] write content_today.json
                               ↓
render_infographic()    → rendered_png  (infographic posts)
generate_ai_image()     → rendered_png  (ai_image posts)
                               ↓
upload_to_github()      → public_image_url  (all posts)
                               ↓
post_to_instagram()     → instagram media ID
post_to_facebook()      → facebook photo ID
                               ↓
write_rotation_log()    → logs updated, run complete
```

---

## Error handling

- If `render_infographic` or `generate_ai_image` returns `None`/`False`: log the failure, skip upload and publish for that post, continue with remaining posts.
- If `upload_to_github` returns `None`: log the failure, skip publish for that post.
- If `post_to_instagram` or `post_to_facebook` returns `None`: log the failure, continue to next post.
- If `fetch_trends` exits early (fewer than 3 fresh candidates): stop the run and notify. Do not proceed to scoring with an insufficient candidate pool.
- Always call `write_rotation_log` at the end even if some posts failed — record whichever posts were successfully published.

---

## Environment variables

All tools load credentials from `.env` in the pipeline directory.

| Variable | Used by tool | Notes |
|---|---|---|
| `BRAVE_SEARCH_API_KEY` | `fetch_trends` | Optional — RSS-only fallback if absent |
| `GEMINI_API_KEY` | `generate_ai_image` | Required for `ai_image` posts |
| `GITHUB_TOKEN` | `upload_to_github` | Required |
| `GITHUB_REPO` | `upload_to_github` | Default: `xhangreichris-max/mak-shang` |
| `GITHUB_POSTS_PATH` | `upload_to_github` | Default: `assets/posts` |
| `META_USER_ACCESS_TOKEN` | `post_to_instagram` | Required. 60-day expiry — refresh before it expires |
| `META_IG_USER_ID` | `post_to_instagram` | Default: `17841421839438768` |
| `META_PAGE_ACCESS_TOKEN` | `post_to_facebook` | Required. 60-day expiry |
| `META_PAGE_ID` | `post_to_facebook` | Default: `1139870945879021` |
| `ANTHROPIC_API_KEY` | **(not used)** | Removed — agent reasons natively in Antigravity |
