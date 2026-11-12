#!/usr/bin/env python3
"""Holt den WoW-Forever-Charakter aus der Blizzard API und schreibt ihn nach data/wow.json.

Konfiguration über .env bzw. Umgebungsvariablen (Fallback: ~/.config/bnet.env):
  BNET_CLIENT_ID      Client-ID von https://develop.battle.net
  BNET_CLIENT_SECRET  Client-Secret
  WOW_CHARACTER       Slug "vorname-nachname" (Standard: fdy-fox)
  WOW_REGION          eu, us, kr, tw (Standard: eu)
"""

import base64
import json
import os
import struct
import sys
import urllib.parse
import urllib.request
import zlib
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

LOCAL = ZoneInfo("Europe/Berlin")

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "wow.json"
IMAGE_DIR = ROOT / "assets" / "wow"
IMAGES = {"avatar": "avatar.jpg", "main-raw": "main.png"}

# Trotz locale=de_DE liefert die API manche Namen nur englisch.
GERMAN = {
    "Alchemy": "Alchemie", "Blacksmithing": "Schmiedekunst", "Enchanting": "Verzauberkunst",
    "Engineering": "Ingenieurskunst", "Herbalism": "Kräuterkunde", "Leatherworking": "Lederverarbeitung",
    "Mining": "Bergbau", "Skinning": "Kürschnerei", "Tailoring": "Schneiderei",
    "Cooking": "Kochkunst", "First Aid": "Erste Hilfe", "Fishing": "Angeln",
}


def trim_png(data, pad=24):
    """Schneidet transparenten Rand ab (nur 8-Bit-RGBA, ohne Pillow). Sonst unverändert zurück."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return data
    pos, idat, ihdr = 8, b"", None
    while pos < len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        chunk = data[pos + 8:pos + 8 + length]
        if kind == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", chunk)
        elif kind == b"IDAT":
            idat += chunk
        pos += length + 12
    width, height, depth, color, _, _, interlace = ihdr
    if (depth, color, interlace) != (8, 6, 0):
        return data

    stride, bpp = width * 4, 4
    raw, rows, prev = zlib.decompress(idat), [], bytearray(stride)
    for y in range(height):
        f, line = raw[y * (stride + 1)], bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if f == 1:
                line[i] = (line[i] + a) & 255
            elif f == 2:
                line[i] = (line[i] + b) & 255
            elif f == 3:
                line[i] = (line[i] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(bytes(line))
        prev = line

    used = [y for y, r in enumerate(rows) if any(r[3::4])]
    if not used:
        return data
    cols = [x for x in range(width) if any(rows[y][x * 4 + 3] for y in used)]
    x0, x1 = max(cols[0] - pad, 0), min(cols[-1] + pad + 1, width)
    y0, y1 = max(used[0] - pad, 0), min(used[-1] + pad + 1, height)

    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))

    body = b"".join(b"\0" + rows[y][x0 * 4:x1 * 4] for y in range(y0, y1))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", x1 - x0, y1 - y0, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(body, 9))
            + chunk(b"IEND", b""))


def load_env():
    for env_file in (ROOT / ".env", Path.home() / ".config" / "bnet.env"):
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip().removeprefix("export ")
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def get(url, headers=None, data=None, raw=False):
    req = urllib.request.Request(url, headers=headers or {}, data=data)
    with urllib.request.urlopen(req, timeout=30) as res:
        body = res.read()
    return body if raw else json.loads(body)


def token(region):
    auth = base64.b64encode(f"{os.environ['BNET_CLIENT_ID']}:{os.environ['BNET_CLIENT_SECRET']}".encode()).decode()
    host = "oauth.battlenet.com.cn" if region == "cn" else "oauth.battle.net"
    res = get(f"https://{host}/token", {"Authorization": "Basic " + auth},
              urllib.parse.urlencode({"grant_type": "client_credentials"}).encode())
    return res["access_token"]


def main():
    load_env()
    for key in ("BNET_CLIENT_ID", "BNET_CLIENT_SECRET"):
        if not os.environ.get(key):
            sys.exit(f"Fehler: {key} fehlt in .env bzw. ~/.config/bnet.env")
    region = os.environ.get("WOW_REGION", "eu")
    slug = os.environ.get("WOW_CHARACTER", "fdy-fox")

    headers = {"Authorization": "Bearer " + token(region)}
    base = f"https://{region}.api.blizzard.com/profile/wow/character/{slug}"
    query = f"?namespace=profile-forever-{region}&locale=de_DE"

    def api(path=""):
        return get(base + path + query, headers)

    profile = api()
    equipment = api("/equipment")
    professions = api("/professions")
    reputations = api("/reputations")
    specs = api("/specializations")
    stats = api("/statistics")
    quests = api("/quests/completed")
    media = api("/character-media")

    # Bilder lokal ablegen, damit Besucher keine Requests an Blizzard auslösen
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    images = {}
    for asset in media.get("assets", []):
        if asset["key"] in IMAGES:
            target = IMAGE_DIR / IMAGES[asset["key"]]
            try:
                image = get(asset["value"], raw=True)
                target.write_bytes(trim_png(image) if target.suffix == ".png" else image)
                images[asset["key"].removesuffix("-raw")] = f"wow/{target.name}"
            except OSError as e:
                print(f"Bild {asset['key']} fehlgeschlagen: {e}", file=sys.stderr)

    active_spec = next((g for g in specs.get("specialization_groups", []) if g.get("is_active")), {})
    spec_names = [s["specialization"]["name"] for s in active_spec.get("specializations", [])]

    def profession(p):
        tier = (p.get("tiers") or [{}])[-1]
        name = p["profession"]["name"]
        return {
            "name": GERMAN.get(name, name),
            "skill": tier.get("skill_points", p.get("skill_points", 0)),
            "max": tier.get("max_skill_points", p.get("max_skill_points", 0)),
        }

    data = {
        "updated": datetime.now(LOCAL).isoformat(timespec="seconds"),
        "character": {
            "name": profile["name"],
            "surname": profile.get("surname", ""),
            "level": profile["level"],
            "race": profile["race"]["name"],
            "class": profile["character_class"]["name"],
            "spec": spec_names[0] if spec_names else "",
            "gender": profile["gender"]["name"],
            "faction": profile["faction"]["name"],
            "guild": profile.get("guild", {}).get("name", ""),
            "ruleset": profile.get("ruleset", {}).get("name", ""),
            "item_level": profile.get("equipped_item_level", 0),
            "achievement_points": profile.get("achievement_points", 0),
        },
        "images": images,
        "stats": {k: stats[k].get("effective", 0) if isinstance(stats.get(k), dict) else stats.get(k, 0)
                  for k in ("health", "power", "strength", "agility", "intellect", "stamina", "spirit", "armor")},
        "power_type": stats.get("power_type", {}).get("name", ""),
        "quests_completed": len(quests.get("quests", [])),
        "professions": {
            "primary": [profession(p) for p in professions.get("primaries", [])],
            "secondary": [profession(p) for p in professions.get("secondaries", [])],
        },
        "equipment": [
            {
                "slot": i["slot"]["name"],
                "name": i["name"],
                "level": i.get("level", {}).get("value", 0),
                "quality": i.get("quality", {}).get("type", "COMMON").lower(),
                "id": i["item"]["id"],
            }
            for i in equipment.get("equipped_items", [])
        ],
        # Nur Fraktionen, bei denen sich schon etwas bewegt hat
        "reputations": sorted(
            (
                {
                    "name": r["faction"]["name"],
                    "standing": r["standing"]["name"],
                    "tier": r["standing"].get("tier", 0),
                    "value": r["standing"].get("value", 0),
                    "max": r["standing"].get("max", 0),
                }
                for r in reputations.get("reputations", [])
                if r["standing"].get("tier", 0) > 3 or r["standing"].get("value", 0) > 0
            ),
            key=lambda r: (-r["tier"], -r["value"]),
        ),
    }

    DATA_FILE.parent.mkdir(exist_ok=True)
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    c = data["character"]
    print(f"→ {c['name']} {c['surname']}, Level {c['level']} {c['class']}, "
          f"{data['quests_completed']} Quests → {DATA_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
