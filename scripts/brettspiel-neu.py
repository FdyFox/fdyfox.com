#!/usr/bin/env python3
"""Legt ein neues Brettspiel im Wiki an und füllt den Steckbrief von BoardGameGeek.

Aufrufe (über make):
  make brettspiel <name>          sucht <name>, übernimmt einen eindeutigen Treffer
                                  (Name darf Leerzeichen haben: make brettspiel Arme Ritter 86322)
  make brettspiel <name> <bgg-id> nimmt genau dieses Spiel, Seite heißt <name>
  make brettspiel <bgg-id>        Seitenname aus dem (deutschen) Spielnamen

Erzeugt content/wiki/brettspiele/<name>/index.md aus archetypes/brettspiel.md und lädt
das Schachtelbild als cover.<ext> daneben. Bewertung und Partien bleiben leer.

Quellen, beide ohne Key:
  - api.geekdo.com: die inoffizielle JSON-API, mit der die BGG-Webseite selbst arbeitet.
    Nicht dokumentiert, kann sich jederzeit ändern – dann hier anpassen.
  - Wikidata: Suche nach Namen (BGG selbst hat keine offene Suche) und deutscher Titel.

  HUGO  Pfad zu hugo (setzt das Makefile)
"""

import json
import os
import re
import subprocess
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SECTION = ROOT / "content" / "wiki" / "brettspiele"
GEEKDO = "https://api.geekdo.com/api"
WIKIDATA = "https://www.wikidata.org/w/api.php"
USER_AGENT = "fdyfox.com-wiki/1.0"


def slugify(text):
    text = text.lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss"), ("&", " und ")):
        text = text.replace(a, b)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def get(url, raw=False, accept="application/json"):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                body = res.read()
            return body if raw else json.loads(body)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 3:  # Rate-Limit
                time.sleep(3 * (attempt + 1))
                continue
            raise


def wikidata(params):
    """Normale Wikidata-API (nicht der SPARQL-Dienst, der bei Last stark drosselt)."""
    return get(f"{WIKIDATA}?{urllib.parse.urlencode(dict(params, format='json'))}")


def wikidata_games(srsearch, limit=10):
    """Brettspiele mit BGG-ID zur Suchanfrage: Liste (bgg-id, deutscher Name, jahr)."""
    found = wikidata({"action": "query", "list": "search", "srlimit": limit,
                      "srsearch": f"{srsearch} haswbstatement:P2339"})["query"]["search"]
    if not found:
        return []
    ids = [h["title"] for h in found]
    entities = wikidata({"action": "wbgetentities", "ids": "|".join(ids),
                         "props": "labels|claims", "languages": "de|en"})["entities"]
    games = []
    for qid in ids:  # Reihenfolge der Suche beibehalten
        e = entities.get(qid, {})
        claims, labels = e.get("claims", {}), e.get("labels", {})

        def first(prop):
            for c in claims.get(prop, []):
                if "datavalue" in c["mainsnak"]:
                    return c["mainsnak"]["datavalue"]["value"]

        bgg, date = first("P2339"), first("P577")
        name = (labels.get("de") or labels.get("en") or {}).get("value")
        if bgg and name:
            games.append((bgg, name, date["time"][1:5] if date else ""))
    return games


def search(name):
    """Treffer zu <name> auf Wikidata. Exakte Namenstreffer getrennt zurück."""
    hits = wikidata_games(name.replace("-", " ").replace('"', ""))
    exact = [h for h in hits if slugify(h[1]) == slugify(name)]
    return exact, hits


def german_name(gid):
    """Deutscher Titel laut Wikidata, falls das Spiel dort steht."""
    try:
        games = wikidata_games(f"haswbstatement:P2339={gid}", limit=1)
    except Exception as e:
        print(f"Hinweis: deutscher Titel nicht von Wikidata geholt ({e})")
        return None
    return games[0][1] if games else None


def thing(gid):
    try:
        item = get(f"{GEEKDO}/geekitems?{urllib.parse.urlencode({'objecttype': 'thing', 'objectid': gid})}")["item"]
    except (urllib.error.HTTPError, KeyError, TypeError):
        item = None
    if not item or not item.get("objectid"):
        sys.exit(f"Kein Spiel mit BGG-ID {gid} gefunden.")
    try:
        stats = get(f"{GEEKDO}/dynamicinfo?{urllib.parse.urlencode({'objecttype': 'thing', 'objectid': gid})}")["item"]["stats"]
    except Exception:  # Komplexität ist nett, aber nicht nötig
        stats = {}

    def num(v):
        try:
            return int(v)
        except (TypeError, ValueError):
            return None

    def links(kind):
        return [l["name"] for l in item.get("links", {}).get(kind, [])
                if not l["name"].startswith("(")]  # "(Uncredited)", "(Unknown)"

    lo, hi = num(item.get("minplayers")), num(item.get("maxplayers"))
    tmin, tmax = num(item.get("minplaytime")), num(item.get("maxplaytime"))
    weight = float(stats.get("avgweight") or 0)
    names = [item["name"]] + [a["name"] for a in item.get("alternatenames", [])]
    return {
        "id": gid,
        "primary": item["name"],
        "names": names,
        "typ": "Erweiterung" if item.get("subtype") == "boardgameexpansion" else "Brettspiel",
        "spieler": (f"{lo}–{hi}" if hi and lo != hi else str(lo)) if lo else None,
        "dauer": f"{tmin}–{tmax}" if tmin and tmax and tmin != tmax else (tmax or tmin),
        "alter": num(item.get("minage")) or None,
        "komplexitaet": round(weight, 1) if weight > 0 else None,
        "autoren": links("boardgamedesigner"),
        "illustration": links("boardgameartist"),
        "verlage": links("boardgamepublisher"),
        "jahr": num(item.get("yearpublished")) or None,
        "image": (item.get("images") or {}).get("original") or item.get("imageurl"),
    }


def german_cover(gid):
    """Bild der neuesten deutschen Ausgabe (BGG führt jede Ausgabe einzeln), sonst None."""
    query = urllib.parse.urlencode({
        "ajax": 1, "nosession": 1, "objecttype": "thing", "objectid": gid, "subtype": "boardgameversion",
        "linkdata_index": "boardgameversion", "pageid": 1, "showcount": 100, "sort": "yearpublished"})
    try:
        versions = get(f"{GEEKDO}/geekitem/linkeditems?{query}").get("items", [])
    except Exception:
        return None
    for v in versions:  # nach Jahr absteigend sortiert
        image = (v.get("images") or {}).get("original")
        if image and re.search(r"\(German\b", v.get("name", "")):
            return image
    return None


def bgg_id(arg):
    """BGG-ID aus einer Zahl oder einer BGG-URL, sonst None."""
    m = re.fullmatch(r"(\d+)", arg) or re.search(r"boardgame(?:expansion)?/(\d+)", arg)
    return m.group(1) if m else None


def yaml_value(v):
    if isinstance(v, (int, float)):
        return str(v)
    return json.dumps(v, ensure_ascii=False)  # JSON-Strings und -Listen sind gültiges YAML


def fill(path, game, title):
    text = path.read_text()
    text = re.sub(r'^title: .*$', f"title: {yaml_value(title)}", text, count=1, flags=re.M)
    values = dict(game, verlag=(game["verlage"] or [None])[0], bgg=int(game["id"]))
    for key in ("typ", "spieler", "dauer", "alter", "komplexitaet", "autoren", "illustration", "verlag", "jahr", "bgg"):
        if values[key] in (None, [], ""):
            continue
        # Nur den Wert im spiel:-Block ersetzen, Kommentare dahinter bleiben stehen
        text = re.sub(rf"^(  {key}:)[^#\n]*?(\s*#.*)?$",
                      lambda m: f"{m.group(1)} {yaml_value(values[key])}{m.group(2) or ''}",
                      text, count=1, flags=re.M)
    path.write_text(text)


def download_cover(url, folder):
    ext = Path(urllib.parse.urlparse(url).path).suffix.lower()
    ext = {".jpeg": ".jpg", "": ".jpg"}.get(ext, ext)
    target = folder / f"cover{ext}"
    target.write_bytes(get(url, raw=True, accept="image/*"))
    return target


def main():
    # make zerlegt "Arme Ritter" in zwei Wörter – deshalb: letzte Angabe ist die ID,
    # wenn sie wie eine aussieht, alles davor ist der Name
    args = sys.argv[1:]
    if not args:
        sys.exit("Aufruf: make brettspiel <name> [<bgg-id>]  oder  make brettspiel <bgg-id>")

    slug, gid, de = None, None, None
    if bgg_id(args[-1]):
        gid, args = bgg_id(args[-1]), args[:-1]
    if args:
        slug = slugify(" ".join(args))

    if not gid:
        try:
            exact, hits = search(slug)
        except Exception as e:
            sys.exit(f"Suche bei Wikidata fehlgeschlagen ({e}). Mit ID aufrufen: make brettspiel {slug} <bgg-id>")
        if len(exact) == 1:
            gid, de = exact[0][0], exact[0][1]
            print(f"Gefunden: {exact[0][1]} ({exact[0][2]}) – BGG-ID {gid}")
        else:
            shown = exact or hits
            if not shown:
                sys.exit(f"Nichts zu „{slug}“ gefunden (Wikidata kennt nicht jedes Spiel).\n"
                         f"BGG-ID aus der Adresse auf boardgamegeek.com nehmen: make brettspiel {slug} <bgg-id>")
            print(f"{'Mehrere' if exact else 'Keine eindeutigen'} Treffer zu „{slug}“ – bitte mit ID aufrufen:")
            for h in shown:
                print(f"  make brettspiel {slugify(h[1])} {h[0]}   # {h[1]}{f' ({h[2]})' if h[2] else ''}")
            sys.exit(1)

    game = thing(gid)
    # Titel: BGG-Name passend zum Seitennamen, sonst deutscher Name (Wikidata), sonst BGG-Hauptname
    # Wikidata nur fragen, wenn kein BGG-Name zum Seitennamen passt (Wikidata drosselt gern)
    title = next((n for n in game["names"] + [de or ""] if slug and slugify(n) == slug), None)
    if not title:
        de = de or german_name(gid)
        title = de or game["primary"]
    slug = slug or slugify(title)

    folder = SECTION / slug
    page = folder / "index.md"
    if page.exists():
        sys.exit(f"Gibt es schon: {page.relative_to(ROOT)}")
    subprocess.run([os.environ.get("HUGO", "hugo"), "new", "--kind", "brettspiel",
                    str(page.relative_to(ROOT))], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)

    fill(page, game, title)
    print(f"→ Steckbrief von BGG übernommen: {title}")
    if len(game["verlage"]) > 1:
        print(f"  Verlag: {game['verlage'][0]} eingetragen, BGG kennt auch: {', '.join(game['verlage'][1:6])}")
    image = german_cover(gid) or game["image"]
    if image:
        try:
            cover = download_cover(image, folder)
            print(f"→ Schachtelbild: {cover.relative_to(ROOT)}")
        except Exception as e:  # Bild ist nett, aber nicht nötig
            print(f"Hinweis: Schachtelbild nicht geladen ({e})")
    print(f"→ Brettspiel erstellt: {page.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
