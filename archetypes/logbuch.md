---
{{- $name := .File.ContentBaseName }}
{{- if findRE `^\d{4}-\d{2}-\d{2}$` $name }}
title: "{{ (time $name).Format "02.01.2006" }}"
{{- else }}
title: "{{ replace $name "-" " " | title }}"
{{- end }}
date: {{ .Date }}
tags: []
draft: true
---
