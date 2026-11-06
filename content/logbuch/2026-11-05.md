---
title: "05.11.2026"
date: 2026-11-05T21:32:12+01:00
tags: ["sicherheit", "linux", "garten", "gaming"]
draft: false
---

Tag drei der Logbuch-Serie - der Vorsatz hält weiter.

## Brotli, die Zweite

Die Brotli-Lücke ([CVE-2026-111497](https://www.cve.org/CVERecord?id=CVE-2026-111497)), je nach Quelle auch HTTP2Shell, Node2Shell oder Broccoli2Shell genannt, hat mich heute erneut beschäftigt.

Um unsere Server zu prüfen, habe ich ein kleines Skript genutzt, das per Ansible auf allen Servern lief. Die Ausgaben habe ich anschließend eingesammelt und ausgewertet. Das Skript schaut sich an:

- installierte Brotli-Pakete (RPM oder Debian) und ob deren Changelog die CVE erwähnt - dann ist der Fix drin,
- welche laufenden Prozesse `libbrotlidec` geladen haben,
- die Node.js-Version,
- Brotli-Pakete für Python (`Brotli`, `brotlicffi`, `brotlipy`),
- installierte .NET-Runtimes,
- und mitgebrachte Kopien von `libbrotlidec` außerhalb von `/usr/lib*` - die gehen bei normalen Paket-Updates nämlich gerne unter.

Vielleicht hilft es ja jemandem:

```sh
#!/bin/sh
echo "=== $(hostname) ==="

echo "--- Pakete mit brotli im Namen (Changelog-Check auf CVE):"
if command -v rpm >/dev/null 2>&1; then
  rpm -qa 2>/dev/null | grep -i brotli | while read -r p; do
    if rpm -q --changelog "$p" 2>/dev/null | grep -q "CVE-2026-111497"; then
      echo "$p  [Changelog nennt CVE -> gepatcht]"
    else
      echo "$p  [Changelog OHNE CVE -> pruefen]"
    fi
  done
elif command -v dpkg-query >/dev/null 2>&1; then
  dpkg-query -W -f='${Package} ${Version}\n' '*brotli*' 2>/dev/null | while read -r n v; do
    if zgrep -qs "CVE-2026-111497" /usr/share/doc/"$n"/changelog.Debian.gz; then
      echo "$n $v  [Changelog nennt CVE -> gepatcht]"
    else
      echo "$n $v  [Changelog OHNE CVE -> pruefen]"
    fi
  done
fi

echo "--- Prozesse, die libbrotlidec geladen haben:"
grep -l libbrotlidec /proc/[0-9]*/maps 2>/dev/null | cut -d/ -f3 | while read -r pid; do
  cat /proc/"$pid"/comm 2>/dev/null
done | sort | uniq -c

echo "--- Node.js:"
command -v node >/dev/null 2>&1 && node -v || echo "kein node"

echo "--- Python-Brotli (pip / brotlicffi):"
for py in python3 python; do
  command -v $py >/dev/null 2>&1 && $py -c 'import importlib.metadata as m
for n in ("Brotli","brotlicffi","brotlipy"):
    try: print(n, m.version(n))
    except Exception: pass' 2>/dev/null
done

echo "--- .NET:"
command -v dotnet >/dev/null 2>&1 && dotnet --list-runtimes || echo "kein dotnet"

echo "--- Gebuendelte/fremde libbrotlidec (ausserhalb /usr/lib*):"
find / -xdev \( -path /proc -o -path /usr/lib -o -path /usr/lib64 \) -prune -o -name 'libbrotlidec*' -print 2>/dev/null
```

## Garten: Diesmal ist die Batterie leer

Im Garten ist heute nicht so viel vorangegangen. Die Tochter unseres Bekannten, der sich um den Gartenumbau kümmert, war leider krank, und er musste sie betreuen und konnte somit erst ab ca. 15 Uhr bei uns sein.

Als wäre das nicht genug, war auch noch die Starterbatterie vom Bagger leer. Gestern der Tank, heute die Batterie. Die Ursache war schnell gefunden: Der Schlüssel stand nicht ganz auf Nullstellung, und so hat der Bagger langsam die Batterie leergezogen.

## Ikea, pünktlich auf die Minute

Die [zweite Ikea-Lieferung](/logbuch/2026-11-04/#ikea-in-drei-teilen) stand heute tatsächlich um 7 Uhr vor der Haustür. Gut, als Lieferzeit war 7 bis 11 Uhr angegeben. Aber seit wann kommt so etwas dann auch wirklich pünktlich um 7?!

## Mehr Leistung für die Grafikkarte?

Zum Schluss bin ich noch über [gpu-unlock](https://github.com/Zagitta/gpu-unlock) gestolpert und habe es direkt bei mir installiert. Ich hoffe, dass es bei meiner RTX 3060 Ti wirklich so viel bringt, wie die README verspricht. Ob das so ist, berichte ich, sobald ich es ausprobiert habe.
