#!/usr/bin/env python3
"""
Tool: read_rotation_log

Reads the archetype rotation log and topic dedup log from the pipeline directory.
Also computes which archetypes are "due" today using least-recently-used order.

Primary function:
    read_rotation_log() -> dict

    Returns:
    {
        "archetype_log": list[dict],   # full contents of archetype-rotation-log.json
        "topic_log": list[dict],        # full contents of trend-topic-log.json
        "due_archetypes": list[str],    # 3 archetypes sorted by how long since last used
    }

    "due_archetypes" is sorted staleness-first: the archetype unused longest comes first.
    This is the ordered list of 3 slots the agent should fill today.
    Returns empty lists for missing or malformed log files (first-run safe).
"""

import json, os, sys

PIPELINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ARCHETYPES = [
    "Trend Spotlight",
    "Myth Buster",
    "Cost & Care Guide",
    "Before You Paint",
    "Local Adaptation",
    "Comparison",
]


def _pick_due_archetypes(archetype_log, count=3):
    last_used = {}
    for entry in archetype_log:
        arch = entry.get("archetype")
        date_str = entry.get("date", "2000-01-01")
        if arch and (arch not in last_used or date_str > last_used[arch]):
            last_used[arch] = date_str
    return sorted(ARCHETYPES, key=lambda a: last_used.get(a, "2000-01-01"))[:count]


def read_rotation_log():
    """
    Read both rotation logs and compute today's due archetypes.
    Returns dict with archetype_log, topic_log, and due_archetypes.
    """
    arch_path = os.path.join(PIPELINE_DIR, "archetype-rotation-log.json")
    topic_path = os.path.join(PIPELINE_DIR, "trend-topic-log.json")

    try:
        with open(arch_path) as f:
            archetype_log = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        archetype_log = []

    try:
        with open(topic_path) as f:
            topic_log = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        topic_log = []

    due_archetypes = _pick_due_archetypes(archetype_log, count=3)

    return {
        "archetype_log": archetype_log,
        "topic_log": topic_log,
        "due_archetypes": due_archetypes,
    }


if __name__ == "__main__":
    result = read_rotation_log()
    print(f"Due archetypes today: {result['due_archetypes']}")
    print(f"Archetype log entries: {len(result['archetype_log'])}")
    print(f"Topic log entries: {len(result['topic_log'])}")
