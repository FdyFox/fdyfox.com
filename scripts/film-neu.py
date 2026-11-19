#!/usr/bin/env python3
"""Legt einen neuen Film im Wiki an und füllt den Steckbrief von TMDB.

Aufrufe (über make):
  make film <name>             sucht <name>, übernimmt einen eindeutigen Treffer
                               (Name darf Leerzeichen haben: make film Zurück in die Zukunft)
  make film <name> <tmdb-id>   nimmt genau diesen Film, Seite heißt <name>
  make film <tmdb-url>         Seitenname aus dem deutschen Titel

Eine reine Zahl allein gilt als Name (make film 1917), nicht als ID – für die ID
die TMDB-Adresse nehmen oder einen Namen davor schreiben.

Erzeugt content/wiki/filme/<name>/index.md aus archetypes/film.md und lädt das
deutsche Poster als cover.jpg daneben. Bewertung und Sichtungen bleiben leer.

Konfiguration über .env bzw. Umgebungsvariablen:
  TMDB_API_KEY  API-Key (v3) oder Lesezugriffs-Token (v4) von themoviedb.org,
                kostenlos unter Einstellungen → API
  HUGO          Pfad zu hugo (setzt das Makefile)
"""

import json
import os
import re
import subprocess
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SECTION = ROOT / "content" / "wiki" / "filme"
API = "https://api.themoviedb.org/3"
IMAGES = "https://image.tmdb.org/t/p/w780"
USER_AGENT = "fdyfox.com-wiki/1.0"
# TMDB liefert Länder nur englisch – die häufigsten auf Deutsch, sonst bleibt der englische Name
LAENDER = {
    "US": "USA", "GB": "Großbritannien", "DE": "Deutschland", "AT": "Österreich", "CH": "Schweiz",
    "FR": "Frankreich", "IT": "Italien", "ES": "Spanien", "NL": "Niederlande", "BE": "Belgien",
    "DK": "Dänemark", "SE": "Schweden", "NO": "Norwegen", "FI": "Finnland", "IE": "Irland",
    "PL": "Polen", "CZ": "Tschechien", "HU": "Ungarn", "CA": "Kanada", "MX": "Mexiko",
    "AU": "Australien", "NZ": "Neuseeland", "JP": "Japan", "KR": "Südkorea", "CN": "China",
    "HK": "Hongkong", "IN": "Indien", "BR": "Brasilien", "AR": "Argentinien", "ZA": "Südafrika",
    "RU": "Russland", "LU": "Luxemburg", "IS": "Island", "TW": "Taiwan",
}


def load_env():
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                # Überschreibt bewusst: VS Code setzt die Werte nur beim Öffnen des Terminals
                os.environ[key.strip()] = value.strip().strip("\"'")


def slugify(text):
    text = text.lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss"), ("&", " und ")):
        text = text.replace(a, b)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def tmdb(path, **params):
    key = os.environ["TMDB_API_KEY"]
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if key.startswith("eyJ"):  # v4-Lesezugriffs-Token (JWT)
        headers["Authorization"] = f"Bearer {key}"
    else:
        params["api_key"] = key
    url = f"{API}{path}?{urllib.parse.urlencode(dict(params, language='de-DE'))}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as res:
        return json.load(res)


def search(name):
    """Treffer zu <name> auf TMDB: Liste (id, titel, originaltitel, jahr). Exakte getrennt."""
    results = tmdb("/search/movie", query=name.replace("-", " "))["results"][:10]
    hits = [(r["id"], r.get("title") or r["original_title"], r["original_title"],
             (r.get("release_date") or "")[:4]) for r in results]
    exact = [h for h in hits if slugify(name) in (slugify(h[1]), slugify(h[2]))]
    return exact, hits


def movie(mid):
    try:
        m = tmdb(f"/movie/{mid}", append_to_response="credits,release_dates")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            sys.exit(f"Kein Film mit TMDB-ID {mid} gefunden.")
        raise

    fsk = None
    for country in m.get("release_dates", {}).get("results", []):
        if country["iso_3166_1"] == "DE":
            certs = [r["certification"] for r in country["release_dates"] if r.get("certification")]
            if certs:
                fsk = int(certs[0]) if certs[0].isdigit() else certs[0]
    crew = m.get("credits", {}).get("crew", [])

    def crew_names(*jobs):
        names = []
        for c in crew:
            if c.get("job") in jobs and c["name"] not in names:
                names.append(c["name"])
        return names

    cast = sorted(m.get("credits", {}).get("cast", []), key=lambda c: c.get("order", 99))
    return {
        "id": m["id"],
        "titel": m.get("title") or m["original_title"],
        "originaltitel": m["original_title"],
        "jahr": int(m["release_date"][:4]) if m.get("release_date") else None,
        "laufzeit": m.get("runtime") or None,
        "fsk": fsk,
        "genres": [g["name"] for g in m.get("genres", [])],
        "regie": crew_names("Director"),
        "drehbuch": crew_names("Screenplay", "Writer"),
        "darsteller": [c["name"] for c in cast[:5]],
        "land": [LAENDER.get(c["iso_3166_1"], c["name"]) for c in m.get("production_countries", [])],
        "tmdb": m["id"],
        "imdb": m.get("imdb_id") or None,
        "poster": m.get("poster_path"),
    }


def tmdb_id(arg):
    """TMDB-ID aus einer Zahl oder einer TMDB-URL, sonst None."""
    m = re.fullmatch(r"(\d+)", arg) or re.search(r"themoviedb\.org/movie/(\d+)", arg)
    return m.group(1) if m else None


def yaml_value(v):
    if isinstance(v, (int, float)):
        return str(v)
    return json.dumps(v, ensure_ascii=False)  # JSON-Strings und -Listen sind gültiges YAML


def fill(path, film):
    text = path.read_text()
    text = re.sub(r'^title: .*$', f"title: {yaml_value(film['titel'])}", text, count=1, flags=re.M)
    for key in ("originaltitel", "jahr", "laufzeit", "fsk", "genres", "regie", "drehbuch",
                "darsteller", "land", "tmdb", "imdb"):
        if film[key] in (None, [], ""):
            continue
        # Nur den Wert im film:-Block ersetzen, Kommentare dahinter bleiben stehen
        text = re.sub(rf"^(  {key}:)[^#\n]*?(\s*#.*)?$",
                      lambda m: f"{m.group(1)} {yaml_value(film[key])}{m.group(2) or ''}",
                      text, count=1, flags=re.M)
    path.write_text(text)


def download_poster(poster_path, folder):
    target = folder / f"cover{Path(poster_path).suffix or '.jpg'}"
    req = urllib.request.Request(IMAGES + poster_path, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as res:
        target.write_bytes(res.read())
    return target


def main():
    load_env()
    if not os.environ.get("TMDB_API_KEY"):
        sys.exit("Fehler: TMDB_API_KEY fehlt in .env (kostenlos auf themoviedb.org → Einstellungen → API)")

    # make zerlegt "Zurück in die Zukunft" in Wörter – deshalb: letzte Angabe ist die ID,
    # wenn sie eine URL ist oder eine Zahl hinter einem Namen, alles davor ist der Name
    args = sys.argv[1:]
    if not args:
        sys.exit("Aufruf: make film <name> [<tmdb-id>]  oder  make film <tmdb-url>")

    slug, mid = None, None
    if "themoviedb.org" in args[-1] or (len(args) > 1 and tmdb_id(args[-1])):
        mid, args = tmdb_id(args[-1]), args[:-1]
    if args:
        slug = slugify(" ".join(args))

    if not mid:
        exact, hits = search(" ".join(args))
        if len(exact) == 1:
            mid = exact[0][0]
            print(f"Gefunden: {exact[0][1]} ({exact[0][3]}) – TMDB-ID {mid}")
        else:
            shown = exact or hits
            if not shown:
                sys.exit(f"Nichts zu „{' '.join(args)}“ gefunden. TMDB-ID aus der Adresse auf "
                         f"themoviedb.org nehmen: make film {slug} <tmdb-id>")
            print(f"{'Mehrere' if exact else 'Keine eindeutigen'} Treffer zu „{' '.join(args)}“ – bitte mit ID aufrufen:")
            for h in shown:
                orig = f" / {h[2]}" if h[2] != h[1] else ""
                print(f"  make film {slugify(h[1])} {h[0]}   # {h[1]}{orig}{f' ({h[3]})' if h[3] else ''}")
            sys.exit(1)

    film = movie(mid)
    # Seitenname wie angegeben, sonst aus dem deutschen Titel
    slug = slug or slugify(film["titel"])

    folder = SECTION / slug
    page = folder / "index.md"
    if page.exists():
        sys.exit(f"Gibt es schon: {page.relative_to(ROOT)}")
    subprocess.run([os.environ.get("HUGO", "hugo"), "new", "--kind", "film",
                    str(page.relative_to(ROOT))], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)

    fill(page, film)
    print(f"→ Steckbrief von TMDB übernommen: {film['titel']}")
    if film["poster"]:
        try:
            cover = download_poster(film["poster"], folder)
            print(f"→ Poster: {cover.relative_to(ROOT)}")
        except Exception as e:  # Poster ist nett, aber nicht nötig
            print(f"Hinweis: Poster nicht geladen ({e})")
    print(f"→ Film erstellt: {page.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
