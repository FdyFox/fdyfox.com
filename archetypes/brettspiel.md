---
title: "{{ replace .File.ContentBaseName "-" " " | title }}"
description: ""
date: {{ .Date }}
draft: true
# Bewertung, je 1–5 (halbe erlaubt). Kriterien stehen in brettspiele/_index.md.
# Gesamt = Durchschnitt; mit "gesamt:" überschreibbar.
bewertung:
{{- with site.GetPage "/wiki/brettspiele" }}
{{- range .Params.kriterien }}
  {{ .key }}:{{ strings.Repeat (int (math.Max 1 (sub 18 (len .key)))) " " }}# {{ .name }}{{ with .beschreibung }} – {{ . }}{{ end }}
{{- end }}
{{- end }}
# Steckbrief – leere Felder werden nicht angezeigt
spiel:
  typ: "Brettspiel"
  spieler: "2–4"
  dauer: 45            # Minuten
  alter: 10
  komplexitaet:        # BGG-Weight, z. B. 1.9 (von 5)
  autoren: []
  illustration: []
  verlag: ""
  jahr:
  bgg:                 # BoardGameGeek-ID aus der URL
# Partien, neueste egal wo – wird nach Datum sortiert
partien:
#  - datum: {{ now.Format "2006-01-02" }}
#    spieler: 4
#    gewonnen: false
#    notiz: ""
# Weitere Bilder: in den Unterordner bilder/ legen und im Text einbinden mit
#   {{ "{{<" }} galerie muster="bilder/*" />{{ "}}" }}
# Bildunterschriften optional in bilder/bildunterschriften.yaml ("datei.jpg: Text").
# cover.* direkt im Ordner ist das Schachtelbild im Steckbrief.
---
