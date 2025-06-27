# Online Shop Buissness Model

**Authors**: Ronny Bruhin, Batuhan Seker

**Date**: 20.06.2025

## 1.  Einleitung

Dieses Dokument beschreibt das Geschäftsprozessmodell eines Onlineshops. Das Modell bildet den Kernprozess einer Online-Bestellung ab, von der Kundeninteraktion bis zur Zahlungsabwicklung. Die Erstellung dieses Modells erfolgte im Rahmen des Moduls "254 - Geschäftsprozesse modellieren" an der Technischen Berufsfachschule Zürich.

### 1.1 Ziel und Nutzen

Ziel dieses Prozesses ist es, die Onlinebestellung effizient, kundenfreundlich und automatisiert abzuwickeln. Der Nutzen besteht in:

- Reduktion von Bearbeitungszeiten
- Klarer Trennung von Verantwortlichkeiten
- Transparenz für Kunden und Betreiber
- Grundlage für Prozessautomatisierung und -optimierung sowie KPI-Überwachung (Key Performance Indicators)

## 2.  Beschreibung des Geschäftsprozesses

Der abgebildete Geschäftsprozess beschreibt den Ablauf einer Bestellung in einem Onlineshop und involviert mehrere Akteure: den **Kunden**, den **Shopbetreiber**, den **Lieferanten** und die **Post**.

Der Prozess beginnt im Pool "Kunde" mit dem Ereignis **"Bestellung aufgeben"**.
    Kunden-Prozess (Pool "Kunde"):
◦
Nach dem Aufgeben der Bestellung wird geprüft, ob der Kunde registriert ist

Ist der Kunde nicht registriert, erfolgt eine "Registrierung abschliessen"-Aktivität

Ist der Kunde registriert (oder hat sich registriert), müssen die "Logindaten eingeben" werden

Anschliessend ist die "Adresse eingeben" notwendig, gefolgt vom "Bestellung prüfen"

Nach der Prüfung der Bestellung führt der Kunde die "Bezahlung durchführen"

Ein Exklusives Gateway prüft, ob die "Zahlung erfolgt" ist
Ist dies nicht der Fall, wird die "Bestellung stornieren"
ausgeführt und der Prozess für diesen Pfad beendet.

Erfolgt die Zahlung, wird die "Bestellung abschliessen"
und das Endereignis "Bestellung abgeschlossen" erreicht

Während des Prozesses sendet der Kunde eine Nachrichtenfluss "Bestellung" an den Geschäftskunden
Auch die Kommunikation über die Zahlung erfolgt via Nachrichtenflüsse zwischen Kunde und Geschäftskunde

**Geschäftskunden-Prozess (Pool "Geschäftskunde"):**

Der Prozess für den Geschäftskunden beginnt mit dem Empfang der "Bestellung erhalten"-Nachricht vom Kunden

Danach wird die "Bestellung prüfen"
 und über ein Exklusives Gateway entschieden, ob die "Bestellung gültig" ist

Ist die Bestellung nicht gültig, wird sie "Bestellung ablehnen"
 und eine Ablehnungsnachricht an den Kunden gesendet

Ist die Bestellung gültig, wird die "Bestellung bestätigen"
 und eine Bestätigungsnachricht an den Kunden gesendet

Anschliessend wird die "Bestellung verarbeiten"

Nach der Verarbeitung wird die "Bestellung versenden"
 Eine Warensendung-Nachricht geht an die Post

Der Geschäftskunde empfängt eine "Wareneingang"-Nachricht von der Post
, was zum Task "Wareneingang prüfen" führt

Parallel dazu wird die "Rechnung erstellen"
 und der "Zahlungseingang prüfen"

Wird der Zahlungseingang nicht innerhalb einer bestimmten Zeit erkannt, wird eine "Mahnung versenden"
 und der Prozess für die "Mahnung verarbeiten"
 fortgesetzt.

Lieferanten-Prozess (Pool "Lieferant"):

Obwohl detaillierte Aufgaben nicht sichtbar sind, ist der Lieferant als Pool vorhanden, was eine Interaktion oder Verantwortlichkeit im Zusammenhang mit der "Bestellung verarbeiten" und "Bestellung versenden" im Geschäftskunden-Pool impliziert

Post-Prozess (Pool "Post"):

Die Post erhält die "Warensendung" vom Geschäftskunden und sendet eine "Wareneingang"-Nachricht an den Geschäftskunden, sobald die Sendung bearbeitet wurde

## 3. Architektur

### 3.1 Setup

Install packages with:

```bash
pip install -r requirements.txt
```

Cd into app directory and start the application with:

```bash
uvicorn main:get_app --reload --factory

```
