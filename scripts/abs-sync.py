#!/usr/bin/env python3
"""Holt Hörbuch-Daten aus Audiobookshelf und schreibt sie nach data/hoerbuecher.json.

Konfiguration über .env bzw. Umgebungsvariablen:
  ABS_URL      z. B. https://audiobookshelf.example.com
  ABS_TOKEN    API-Token (Audiobookshelf → Einstellungen → Benutzer → API-Token)
  ABS_LIBRARY  optional: Name der Bibliothek (Standard: erste Hörbuch-Bibliothek)
"""

import json
import os
import sys
import urllib.request
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "hoerbuecher.json"
COVER_DIR = ROOT / "assets" / "hoerbuecher" / "covers"
WEEKDAYS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
TRANSLATOR_MARKERS = ("übersetzer", "translator")
MONTHS = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]


def load_env():
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def api(path, raw=False):
    req = urllib.request.Request(
        os.environ["ABS_URL"].rstrip("/") + path,
        headers={"Authorization": "Bearer " + os.environ["ABS_TOKEN"]},
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        body = res.read()
    return body if raw else json.loads(body)


def split_authors(author_name):
    """Zerlegt "A, B - Übersetzer" in (Autor:innen, Übersetzer:innen)."""
    authors, translators = [], set()
    for name in (author_name or "").split(","):
        name = name.strip()
        base = name.rsplit(" - ", 1)[0].strip() if " - " in name else name
        if not base:
            continue
        if any(m in name.lower() for m in TRANSLATOR_MARKERS):
            translators.add(base)
        else:
            authors.append(base)
    return authors, translators


def from_ms(ms):
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc) if ms else None


def heatmap(days):
    """Raster der letzten 12 Monate, Wochen als Spalten (Mo–So)."""
    today = date.today()
    start = today - timedelta(days=364)
    start -= timedelta(days=start.weekday())
    minutes = {d: round(sec / 60) for d, sec in days.items() if d >= start.isoformat()}

    # Stufen nach der eigenen Verteilung (Quartile der Hörtage), nicht nach festen Stunden
    values = sorted(m for m in minutes.values() if m > 0)
    bounds = [values[len(values) * q // 4] for q in (1, 2, 3)] if values else []

    weeks = []
    day = start
    while day <= today:
        week = {"month": "", "days": []}
        for _ in range(7):
            if day > today:
                break
            if day.day == 1:
                week["month"] = MONTHS[day.month - 1]
            m = minutes.get(day.isoformat(), 0)
            duration = f"{m} min" if m < 60 else f"{m / 60:.1f} h".replace(".", ",")
            week["days"].append({
                "t": f"{WEEKDAYS[day.weekday()]} {day:%d.%m.%Y} · {duration if m else 'nichts gehört'}",
                "l": 1 + sum(m > b for b in bounds) if m else 0,
            })
            day += timedelta(days=1)
        weeks.append(week)

    return {"weeks": weeks, "active_days": len(values)}


def main():
    load_env()
    for key in ("ABS_URL", "ABS_TOKEN"):
        if not os.environ.get(key):
            sys.exit(f"Fehler: {key} fehlt in .env")

    libraries = [l for l in api("/api/libraries")["libraries"] if l["mediaType"] == "book"]
    wanted = os.environ.get("ABS_LIBRARY")
    library = next((l for l in libraries if not wanted or l["name"] == wanted), None)
    if not library:
        sys.exit(f"Fehler: keine Hörbuch-Bibliothek gefunden ({wanted or 'beliebig'})")

    items = api(f"/api/libraries/{library['id']}/items?limit=0")["results"]
    progress = {p["libraryItemId"]: p for p in api("/api/me")["mediaProgress"] if not p.get("episodeId")}
    listening = api("/api/me/listening-stats")

    # Übersetzer:innen sammeln, damit sie auch ohne Zusatz ("A, B") erkannt werden
    translators = set()
    for item in items:
        translators |= split_authors(item["media"]["metadata"].get("authorName"))[1]

    COVER_DIR.mkdir(parents=True, exist_ok=True)
    books = []
    used_covers = set()
    for item in items:
        meta = item["media"]["metadata"]
        p = progress.get(item["id"], {})
        finished = from_ms(p.get("finishedAt")) if p.get("isFinished") else None
        listening_now = not finished and (p.get("progress") or 0) > 0

        # Cover nur für "Gerade am Hören"
        cover = None
        if listening_now and item["media"].get("coverPath"):
            cover_file = COVER_DIR / f"{item['id']}.jpg"
            if not cover_file.exists():
                try:
                    cover_file.write_bytes(api(f"/api/items/{item['id']}/cover?width=400&format=jpeg", raw=True))
                except OSError as e:
                    print(f"Cover für {meta.get('title')} fehlgeschlagen: {e}", file=sys.stderr)
            if cover_file.exists():
                cover = f"hoerbuecher/covers/{cover_file.name}"
                used_covers.add(cover_file.name)

        authors = [a for a in split_authors(meta.get("authorName"))[0] if a not in translators]
        books.append({
            "title": meta.get("title") or "Unbekannt",
            "author": ", ".join(authors) or "Unbekannt",
            "_authors": authors,
            "series": meta.get("seriesName") or "",
            "narrator": meta.get("narratorName") or "",
            "year": meta.get("publishedYear") or "",
            "language": meta.get("language") or "",
            "genres": meta.get("genres") or [],
            "hours": round((item["media"].get("duration") or 0) / 3600, 1),
            "added": from_ms(item.get("addedAt")).date().isoformat() if item.get("addedAt") else "",
            "finished": finished.date().isoformat() if finished else "",
            "progress": round((p.get("progress") or 0) * 100),
            "cover": cover,
            "_last": p.get("lastUpdate") or 0,
        })

    finished_books = sorted((b for b in books if b["finished"]), key=lambda b: b["finished"], reverse=True)
    # "Gerade am Hören": zuletzt gehört zuerst
    in_progress = sorted(
        (b for b in books if not b["finished"] and b["progress"] > 0),
        key=lambda b: b["_last"], reverse=True,
    )
    authors_by_book = []
    for b in books:
        del b["_last"]
        authors_by_book.append(b.pop("_authors"))
    for f in COVER_DIR.glob("*.jpg"):
        if f.name not in used_covers:
            f.unlink()

    hours_per_year = defaultdict(float)
    for day, seconds in listening.get("days", {}).items():
        hours_per_year[day[:4]] += seconds / 3600

    finished_authors = Counter(
        a for b, authors in zip(books, authors_by_book) if b["finished"] for a in authors
    )
    series = Counter(b["series"].split(" #")[0] for b in finished_books if b["series"])

    data = {
        "updated": datetime.now(timezone.utc).date().isoformat(),
        "totals": {
            "books": len(books),
            "finished": len(finished_books),
            "library_hours": round(sum(b["hours"] for b in books)),
            "listened_hours": round(listening.get("totalTime", 0) / 3600),
        },
        "finished_per_year": sorted(Counter(b["finished"][:4] for b in finished_books).items(), reverse=True),
        "hours_per_year": sorted(((y, round(h)) for y, h in hours_per_year.items()), reverse=True),
        "top_authors": finished_authors.most_common(10),
        "top_series": series.most_common(10),
        "languages": Counter(b["language"] for b in books if b["language"]).most_common(),
        "in_progress": in_progress,
        "heatmap": heatmap(listening.get("days", {})),
    }

    DATA_FILE.parent.mkdir(exist_ok=True)
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(f"→ {len(books)} Hörbücher, {len(finished_books)} gehört → {DATA_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
