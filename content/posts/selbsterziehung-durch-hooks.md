---
title: "Selbsterziehung durch Hooks"
date: 2026-10-22T09:30:00+02:00
tags: ["git", "linux", "tipps"]
draft: false
---

Ich habe ein paar Git-Hooks, die global für alle meine Repos gelten. Die Idee dahinter ist simple Selbsterziehung: Wenn ich mich nicht an die Regeln halte, lässt Git mich einfach nicht committen.

```bash {title="Hooks global aktivieren"}
git config --global core.hooksPath ~/.config/git/hooks
```

Im Ordner liegen zwei Hooks:

- **pre-commit** entfernt Leerzeichen am Zeilenende, sorgt für genau einen Zeilenumbruch am Dateiende und zählt bei Bedarf eine Versionsnummer hoch.
- **commit-msg** prüft, ob die Commit-Nachricht dem [Conventional-Commits](https://www.conventionalcommits.org/)-Format folgt, also `feat(scope): beschreibung`.

Das funktioniert seit einer Weile gut. Dachte ich jedenfalls.

## feat(wiki): add wiki section

Beim Commit für das neue Wiki hier auf der Seite kam plötzlich das:

```text
🚫 Commit message does not follow the conventional format.
Requested pattern is: type(scope): subject
```

Für `feat(wiki): add wiki section`. Typ passt, Scope passt, Doppelpunkt und Leerzeichen sind da. Was soll daran falsch sein?

Der Übeltäter steckt im Regex:

```bash {title="commit-msg (vorher)"}
PATTERN_STRING="^(feat|fix|build|chore|docs|style|refactor|perf|test)\(.*\): (.+[^.\r\n])([\r\n]+(.+[\r\n]+)+)?$"
```

Der Teil `[^.\r\n]` soll sagen: „Die Betreffzeile darf nicht mit einem Punkt oder Zeilenumbruch enden.“ Nur kennt `grep -E` innerhalb von eckigen Klammern keine Escape-Sequenzen. `\r` ist dort kein Carriage Return, sondern einfach ein Backslash und ein `r`. Die Klammer verbietet also am Ende: `.`, `\`, `r` und `n`.

Heißt im Klartext: **Jede Commit-Nachricht, die auf „n“ oder „r“ endet, wird abgelehnt.** `add wiki section`, `fix login button`, `update footer`, `handle error` - alles raus. Hooks erziehen eben - manchmal auch zu Dingen, die man gar nicht wollte.

## Und noch ein Loch

Beim Reparieren fiel noch etwas auf: `grep` arbeitet zeilenweise. Bei einer mehrzeiligen Commit-Nachricht reicht es also, wenn *irgendeine* Zeile dem Muster entspricht. Die erste Zeile kann kompletter Unsinn sein, solange weiter unten im Text eine gültige Zeile steht.

Der Teil `([\r\n]+(.+[\r\n]+)+)?`, der eigentlich den Nachrichtentext abdecken sollte, hat aus demselben Grund nie etwas bewirkt.

## Der Fix

Beides lässt sich mit zwei kleinen Änderungen beheben: Den Regex auf die Betreffzeile reduzieren und nur die erste Zeile prüfen.

```bash {title="commit-msg (nachher)"}
PATTERN_STRING="^(feat|fix|build|chore|docs|style|refactor|perf|test)\(.*\): (.+[^.])$"

if ! echo "$commit_msg" | head -n1 | grep -qE "$PATTERN_STRING"; then
    # ...
fi
```

Getestet mit ein paar Beispielen:

| Nachricht | Ergebnis |
|---|---|
| `feat(wiki): add wiki section` | ok |
| `fix(css): fix color` | ok |
| `feat(x): ends with dot.` | abgelehnt |
| `feature(x): wrong type` | abgelehnt |
| `feat: no scope` | abgelehnt |
| Unsinn in Zeile 1, gültige Zeile darunter | abgelehnt |

## Wenn man schon mal dabei ist

Wer einmal genauer hinschaut, findet natürlich mehr. Drei Dinge habe ich gleich mit repariert:

**Merge-Ausnahme:** Stand irgendwo in der Nachricht das Wort „merge“, wurde gar nicht mehr geprüft - auch bei `feat(sort): add merge sort`. Jetzt zählen nur noch Nachrichten, die Git selbst erzeugt:

```bash {title="commit-msg"}
if echo "$commit_msg" | head -n1 | grep -qE "^Merge "; then
    exit 0
fi
```

**WIP-Sperre:** Die Prüfung auf „WIP“ hat die ganze Nachricht durchsucht, auch mitten in Wörtern. `add swipe gesture` war damit nicht drin. Jetzt prüft sie nur die Betreffzeile und nur ganze Wörter (`-w`):

```bash {title="commit-msg"}
if echo "$commit_msg" | head -n1 | grep -qiw "wip"; then
```

**Partielles Staging:** Die pre-commit-Fixer machen am Ende ein `git add` auf die *ganze* Datei. Wer mit `git add -p` nur einen Teil einer Datei committen wollte, hatte trotzdem alles im Commit. Jetzt werden teilweise gestagte Dateien übersprungen:

```bash {title="trailing-whitespace-fixer.sh / end-of-file-fixer.sh"}
for FILE in $FILES; do
    # Skip partially staged files, otherwise git add would commit the whole file
    if ! git diff --quiet -- "$FILE"; then
        printf "⚠️  Skipped %s (partially staged).\n" "$FILE"
        continue
    fi
    # ...
done
```

Die Leerzeichen in so einer Datei bleiben dann eben bis zum nächsten Commit drin. Lieber das, als Code im Commit, der da nicht hingehört.

Selbsterziehung funktioniert also - man sollte nur ab und zu prüfen, wozu man sich eigentlich erzieht.
