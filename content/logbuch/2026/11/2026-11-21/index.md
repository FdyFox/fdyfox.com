---
title: "21.11.2026"
date: 2026-11-21T23:45:00+01:00
tags: ["familie", "gaming", "meta"]
draft: false
---

Heute gibt es einen Kindergeburtstag, eine Runde mit den Hunden, schon wieder einen neuen WoW-Charakter und ein kleines DNS-Rätsel.

## Ein kleines Wunder

Heute ist etwas Außergewöhnliches passiert: Ich konnte doch tatsächlich bis 10 Uhr im Bett bleiben! Mit zwei Kindern ist das schon ein kleines Wunder :)

Normalerweise ist spätestens am frühen Morgen jemand wach, der Hunger hat, spielen will oder einfach findet, dass ich jetzt auch aufstehen sollte.

## Geburtstag und Gassirunde

Robin war auf einen Kindergeburtstag eingeladen, und Sonja hat ihn begleitet. Es ging ins [Erlebnisbergwerk Velsen](https://www.erlebnisbergwerkvelsen.de/) in Saarbrücken-Klarenthal, und die Führung war toll, wie mir berichtet wurde!

Velsen ist ein ehemaliges Steinkohlebergwerk. Heute bietet es [extra Führungen für Kindergeburtstage](https://www.erlebnisbergwerkvelsen.de/Events/Kindergeburtstag/) an, und das hat sich gelohnt: Robin ist unter Tage mit der Grubenbahn gefahren und durfte einige der alten Bergbaumaschinen selbst bedienen - für Kinder natürlich ein Highlight. Hier im Saarland gehört der Bergbau einfach zur Geschichte dazu, und so etwas mal aus der Nähe zu sehen, finde ich super.

Ich bin in der Zeit zusammen mit Hanna mit den Hunden raus, da das Wetter heute zur Abwechslung mal echt schön war. Nach den vielen grauen und nassen Novembertagen tat es richtig gut, mal wieder Sonne abzubekommen. Die Hunde hatten ihren Spaß, Hanna auch, und ich habe die ruhige Zeit mit ihr sehr genossen.

## WoW: Gruppenzwang bei der Allianz

Mein dritter WoW-Charakter lebt: Ihr Name ist [Ferdy Fox](/wiki/spiele/wow-forever/ferdy-fox/), eine Himmelsgeborene des Hohen Ordens. Schon wieder ein Magier, diesmal aber auf der Seite der Allianz. Bisher waren meine Schamanin und mein Untoter [Magier Merlin Fox](/logbuch/2026-11-18/#wow-zurück-zum-magier) nämlich beide bei der Horde unterwegs.

Warum also der Seitenwechsel? Gruppenzwang! Tatsächlich haben sich dort drei Personen eingenistet, die ich gut kenne. Außerdem ist es ganz schön, mal andere Gebiete zu sehen. Mit der Horde kenne ich die Startgebiete inzwischen ja fast auswendig, bei der Allianz ist dagegen vieles neu.

Level 10 hat Ferdy schon erreicht. Mal sehen, wie weit sie in den nächsten Tagen kommt :)

## DNS4EU und die falsche Adresse

Heute Abend hat mich Massimo von [kobaltauge.de](https://www.kobaltauge.de) angeschrieben, dass er eine Fehlermeldung bekommt, wenn er meinen Blog öffnet. Nachdem er ein wenig herumgetestet hat, stellte sich heraus, dass der DNS-Anbieter [DNS4EU](https://www.joindns4.eu/) beim Aufruf der Domain eine falsche IP-Adresse zurückgibt. Als ich es am Abend selbst geprüft habe, wurde die richtige IP-Adresse angezeigt. Ganz komisch, das Ganze.

Meine Vermutung: DNS4EU gibt es in mehreren Varianten, und die meisten davon filtern - etwa Malware, Phishing oder Werbung. Landet eine Domain dort (vielleicht auch nur fälschlicherweise) auf einer Sperrliste, antwortet der Resolver nicht mit der echten Adresse, sondern mit der IP einer eigenen Blockseite. Der Browser meckert dann, weil das Zertifikat nicht zu fdyfox.com passt - genau so eine Fehlermeldung. Wird der Eintrag später wieder entfernt, ist alles wieder normal, und beim Nachprüfen sieht man nichts mehr.

Möglich wäre auch, dass einer der DNS4EU-Server einfach noch eine alte oder kaputte Antwort im Cache hatte, während andere schon die richtige Adresse kannten. Je nachdem, bei welchem Server man landet, bekommt man dann unterschiedliche Ergebnisse. Sicher weiß ich es nicht - danke aber an Massimo fürs Bescheidsagen und Herumtesten!
