---
title: "{{ replace .File.ContentBaseName "-" " " | title }}"
description: ""
date: {{ .Date }}
draft: true
# Bewertung 1–5 (halbe erlaubt)
bewertung:
# Steckbrief – leere Felder werden nicht angezeigt
film:
  originaltitel: ""    # nur angezeigt, wenn er vom Titel abweicht
  jahr:
  laufzeit:            # Minuten
  fsk:
  genres: []
  regie: []
  drehbuch: []
  darsteller: []
  land: []
  tmdb:                # TMDB-ID aus der URL
  imdb: ""             # z. B. tt0133093
# Wann wir ihn gesehen haben – wird nach Datum sortiert
gesehen:
#  - datum: {{ now.Format "2006-01-02" }}
#    wo: "Kino"
#    notiz: ""
---
