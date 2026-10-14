#!/usr/bin/env python3
"""Merge shared non-secret Pi preferences into the current agent settings."""

from pathlib import Path
from datetime import datetime
import json
import os
import shutil
import tempfile
import sys


def main() -> int:
    repo = Path(os.environ.get("PI_AGENT_COLLECTION_DIR", Path(__file__).resolve().parent)).expanduser().resolve()
    shared_path = repo / "config" / "settings.json"
    agent_dir = Path(
        os.environ.get("PI_CODING_AGENT_DIR", Path.home() / ".pi/agent")
    ).expanduser()
    target = agent_dir / "settings.json"
    if not shared_path.is_file():
        print("Shared settings are missing; run ./update.py first.", file=sys.stderr)
        return 1
    try:
        shared = json.loads(shared_path.read_text())
        current = json.loads(target.read_text()) if target.exists() else {}
    except (OSError, json.JSONDecodeError):
        print("Could not read valid Pi settings JSON.", file=sys.stderr)
        return 1
    if not isinstance(shared, dict) or not isinstance(current, dict):
        print("Pi settings must be JSON objects.", file=sys.stderr)
        return 1

    agent_dir.mkdir(parents=True, exist_ok=True)
    had_settings = target.exists()
    if had_settings:
        backup = target.with_name(f"settings.json.bak-{datetime.now():%Y%m%d-%H%M%S-%f}")
        shutil.copy2(target, backup)
    current.update(shared)
    with tempfile.NamedTemporaryFile("w", dir=agent_dir, delete=False) as temporary:
        json.dump(current, temporary, indent=2)
        temporary.write("\n")
        temp_path = Path(temporary.name)
    os.replace(temp_path, target)
    print(
        "Merged shared preferences into Pi settings; existing settings were backed up."
        if had_settings else "Created Pi settings with shared preferences."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
