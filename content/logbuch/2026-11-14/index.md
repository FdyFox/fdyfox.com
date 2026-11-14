---
title: "14.11.2026"
date: 2026-11-14T21:25:52+01:00
tags: ["haus", "photovoltaik", "familie", "ausflug", "selfhosting", "meta"]
draft: false
---

Tag zwölf der Logbuch-Serie - ein Samstag zwischen Wasserschaden, Industriekultur und ein paar Basteleien hier an der Seite.

## Wasserschaden: Die Profis sollen ran

Eigentlich hatte ich mir ja vorgenommen, mich erst am Montag um den [Schaden im Keller](/logbuch/2026-11-13/#volltreffer-ins-abwasser) zu kümmern. Ganz losgelassen hat mich das Thema über Nacht aber nicht, und so habe ich heute Morgen doch schon zum Telefon gegriffen und eine Firma angerufen. Sie soll vorbeikommen, sich das Ganze in Ruhe anschauen und mir ein Angebot machen, wie und zu welchem Preis sich der Schaden beheben lässt.

Den Tipp mit [Polygon](https://www.polygongroup.com/de-DE/) habe ich von einem Freund bekommen, der mit der Firma gute Erfahrungen gemacht hat.

Je länger ich darüber nachdenke, desto mehr frage ich mich allerdings, ob es nicht so langsam Zeit wird, für die ganze Geschichte einen Anwalt und einen Gutachter hinzuzuziehen.

## Ein Tag in der Völklinger Hütte

Wie [gestern schon angekündigt](/logbuch/2026-11-13/#raclette-saison-eröffnet), haben wir uns heute zusammen mit unserem Besuch die Völklinger Hütte angeschaut. Für alle, die sie nicht kennen: Das alte Eisenwerk mitten in Völklingen ist seit 1994 UNESCO-Weltkulturerbe und heute eines der bekanntesten Ausflugsziele hier im Saarland.

Und ich kann nur sagen: Es ist wirklich ein sehr beeindruckendes Bauwerk. Schon von außen wirken die riesigen Hochöfen gewaltig, und sobald man drinnen über die Treppen und Stege läuft, merkt man erst, wie groß die Anlage eigentlich ist. Man ist locker einige Stunden damit beschäftigt, alles zu erkunden - und entdeckt trotzdem an jeder Ecke noch etwas Neues. Mal ist es eine alte Rangierlok, mal ein verrosteter Schaltkasten, mal einfach nur ein schöner Ausblick über die Stadt.

Ich habe natürlich jede Menge Fotos gemacht. Eine Auswahl davon findest du hier:

{{< galerie muster="bilder/*" />}}

Falls du in der Gegend bist und noch nie dort warst: Plan dir auf jeden Fall genug Zeit ein, es lohnt sich. :)

## FreshRSS im Testlauf

Gestern Nacht, als alle schon im Bett waren, habe ich mir noch eine Instanz von [FreshRSS](https://freshrss.org/) in meinem Homelab aufgesetzt. FreshRSS ist ein Feedreader, den man selbst hosten kann: Man abonniert darin die RSS-Feeds von Blogs und Webseiten und bekommt alle neuen Beiträge gesammelt an einem Ort angezeigt, ohne dass ein Algorithmus dazwischenfunkt.

Läuft wie die meisten meiner Dienste als Docker-Container und holt sich zweimal pro Stunde die neuen Beiträge. Jetzt will ich die Anwendung erst einmal ein paar Tage im Alltag testen und schauen, ob sie mir zusagt.

## Neues auf der Seite

Neben dem Ausflug habe ich heute auch wieder einiges an dieser Seite geschraubt. Damit du nicht selbst suchen musst, hier eine kurze Übersicht:

- **WoW Forever:** Die Seite zu meinen Charakteren hat ein komplett neues Design bekommen, angelehnt an die Tooltips aus dem Spiel und mit passender Schrift. Außerdem kann ich jetzt mehrere Charaktere anzeigen: Auf der Übersicht wählst du einen aus, ähnlich wie beim Login im Spiel, und jeder Charakter hat seine eigene Seite. Schau gern mal [im Wiki](/wiki/spiele/wow-forever/) vorbei.
- **Wiki-Übersicht:** Die einzelnen Bereiche des Wikis werden jetzt als Karten dargestellt, und die letzten Änderungen stehen gesammelt in einem gemeinsamen Kasten.
- **Einheitlicher Look:** [/now](/now/), [/uses](/uses/) und die Seite [Zu Hause](/wiki/homelab/zu-home/) zu meinem Homelab haben ein gemeinsames Karten-Design bekommen und sehen jetzt endlich aus wie aus einem Guss.
- **Bildergalerien:** Beiträge können jetzt Galerien mit Vorschaubildern und einer Vollbildansicht haben - die erste davon siehst du weiter oben bei der Völklinger Hütte.
- **Changelog:** Unter [/changelog](/changelog/) steht ab sofort alles, was sich an der Seite selbst geändert hat. Die Einträge schreibe ich direkt in meine Commit-Messages, von dort landen sie automatisch auf der Seite.
- **Slashes:** Unter [/slashes](/slashes/) gibt es nach dem Vorbild von [slashpages.net](https://slashpages.net/) eine Übersicht aller festen Seiten. Im Menü findest du sie unter `~/*`.
