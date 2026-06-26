#!/usr/bin/env python3
"""
Tool: write_rotation_log

Appends today's published posts to the archetype rotation log and topic dedup log,
and writes a permanent archive to published/YYYY-MM-DD.json.
Keeps the archetype log capped at 60 entries and the topic log at 90 entries.
Call this once at the end of each daily run, after all posts have been published.

Primary function:
    write_rotation_log(posts: list[dict]) -> bool

    posts: list of post dicts, each containing at minimum:
        "archetype"    (str): the assigned archetype name
        "source_title" (str): the original source article title
        "date"         (str): ISO date string (YYYY-MM-DD)

    Also reads from each post (if present):
        "output_format", "source_url", "caption", "hashtags",
        "public_image_url", "rendered_png", "publish_result"

    Returns True on success, False on failure.
    Reads/writes archetype-rotation-log.json and trend-topic-log.json
    in the pipeline directory. Also writes published/YYYY-MM-DD.json.
    The published/ directory is created automatically on first use.
"""

import json, os, sys, datetime

PIPELINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _write_published_archive(posts):
    """
    Write published/YYYY-MM-DD.json with the final post data for today's run.
    Creates the published/ directory if it doesn't exist.
    Archive write failures are printed but do not affect the rotation-log return value.
    """
    date = posts[0].get("date") if posts else datetime.date.today().isoformat()
    published_dir = os.path.join(PIPELINE_DIR, "published")
    os.makedirs(published_dir, exist_ok=True)
    archive_path = os.path.join(published_dir, f"{date}.json")

    REQUIRED_ARCHIVE_FIELDS = ("caption", "hashtags", "public_image_url", "rendered_png")

    archive = []
    for post in posts:
        archetype = post.get("archetype", "?")
        missing = [f for f in REQUIRED_ARCHIVE_FIELDS if not post.get(f)]
        if missing:
            print(f"WARNING: post '{archetype}' is missing {missing} — archive entry will be incomplete.")
        archive.append({
            "archetype":        post.get("archetype", ""),
            "output_format":    post.get("output_format", ""),
            "source_title":     post.get("source_title", ""),
            "source_url":       post.get("source_url", ""),
            "date":             post.get("date", date),
            "caption":          post.get("caption", ""),
            "hashtags":         post.get("hashtags", ""),
            "public_image_url": post.get("public_image_url"),
            "rendered_png":     post.get("rendered_png"),
            "publish_result":   post.get("publish_result", {}),
        })

    try:
        with open(archive_path, "w", encoding="utf-8") as f:
            json.dump(archive, f, indent=2, ensure_ascii=False)
        print(f"Published archive written: {archive_path}")
    except Exception as e:
        print(f"ERROR writing published archive: {e}")


def write_rotation_log(posts):
    """
    Append today's posts to both rotation logs.
    Returns True on success, False on failure.
    """
    now = datetime.datetime.utcnow().isoformat() + "Z"

    arch_path = os.path.join(PIPELINE_DIR, "archetype-rotation-log.json")
    try:
        with open(arch_path) as f:
            arch_log = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        arch_log = []

    topic_path = os.path.join(PIPELINE_DIR, "trend-topic-log.json")
    try:
        with open(topic_path) as f:
            topic_log = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        topic_log = []

    for post in posts:
        date = post.get("date", datetime.date.today().isoformat())
        arch_log.append({
            "date": date,
            "archetype": post.get("archetype", ""),
            "generated_at": now,
        })
        topic_log.append({
            "date": date,
            "topic": post.get("source_title", ""),
            "archetype": post.get("archetype", ""),
            "generated_at": now,
        })

    arch_log = arch_log[-60:]
    topic_log = topic_log[-90:]

    try:
        with open(arch_path, "w") as f:
            json.dump(arch_log, f, indent=2)
        with open(topic_path, "w") as f:
            json.dump(topic_log, f, indent=2)
        print(f"Rotation logs updated: {len(posts)} entries added.")
    except Exception as e:
        print(f"ERROR writing rotation logs: {e}")
        return False

    _write_published_archive(posts)
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python tools/write_rotation_log.py <content_today.json>")
        sys.exit(1)
    with open(sys.argv[1], encoding="utf-8") as f:
        posts = json.load(f)
    success = write_rotation_log(posts)
    sys.exit(0 if success else 1)
