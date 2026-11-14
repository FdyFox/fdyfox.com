#!/usr/bin/env python3
"""Sammelt "Changelog:"-Zeilen aus den Commit-Messages nach data/changelog.json.

Ein Commit taucht im Changelog auf, wenn seine Message im letzten Absatz eine
oder mehrere Trailer-Zeilen enthält:

    feat(): Add gallery shortcode

    Changelog: Beiträge können jetzt Bildergalerien haben.

Ältere Einträge von vor dieser Konvention stehen in data/changelog_history.yaml.
"""

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "changelog.json"

FIELD, RECORD = "\x1f", "\x1e"


def main():
    log = subprocess.run(
        ["git", "log", "--date=short",
         f"--format=%h{FIELD}%ad{FIELD}%(trailers:key=Changelog,valueonly,separator=%x1f){RECORD}"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout

    entries = []
    for record in log.split(RECORD):
        parts = record.strip("\n").split(FIELD)
        if len(parts) < 3:
            continue
        commit, date, *texts = parts
        for text in texts:
            text = " ".join(text.split())
            if text:
                entries.append({"date": date, "commit": commit, "text": text})

    DATA_FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
    print(f"→ {len(entries)} Changelog-Einträge aus Git → {DATA_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
