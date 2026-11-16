---
{{- $name := .File.ContentBaseName }}
{{- $day := now.Format "2006-01-02" }}
{{- if findRE `^\d{4}-\d{2}-\d{2}$` $name }}
{{- $day = $name }}
title: "{{ (time $name).Format "02.01.2006" }}"
{{- else }}
title: "{{ replace $name "-" " " | title }}"
{{- end }}
{{- /* Logbuch-Einträge erscheinen immer um 21 Uhr deutscher Zeit */}}
date: {{ time.AsTime (printf "%sT21:00:00" $day) "Europe/Berlin" | time.Format "2006-01-02T15:04:05-07:00" }}
tags: []
draft: true
---

Stichpunkte:
