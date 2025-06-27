**Date:** 27-06-2025  
**Author:** Batuhan Seker  

# OnlineShop & Prozessautomatisierung mit Camunda

## Entwicklungsprozess

Wir haben eine **CRUD**-ähnliche Applikation mit Fokus auf das Backend entwickelt. Das **BPMN-Modell** stand zunächst nicht im Vordergrund, wurde aber später zentral für die Prozesssteuerung.

### Technologien

- **Programmiersprache:** Python  
    - Python wurde wegen seiner Einfachheit gewählt, um möglichst wenig Zeit für das Backend und mehr für die Prozessmodellierung zu haben.
    - 📚 **Wichtige Bibliotheken:**
        - `camunda-external-task-client-python3`: Für die Integration mit der Camunda Process Engine
        - `uvicorn`: Asynchroner Webserver
        - `sqlite3`: Datenbankanbindung
        - `fastapi`: Webframework für APIs
- **Datenbank:** SQLite  
    - SQLite ist serverlos, benötigt keine komplexe Einrichtung und speichert alles in einer einzigen Datei, was die Verteilung vereinfacht.

### Die Datenbank

Als ersten Schritt haben wir die Datenbank festgelegt:

```sql
DROP TABLE IF EXISTS products;
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL,
    stock INTEGER NOT NULL,
    added_date DATE NOT NULL DEFAULT (DATE('now'))
);

INSERT INTO products (name, description, price, stock) VALUES 
    ('Gaming Mouse', 'High precision wireless gaming mouse', 49.99, 25),
    ('Mechanical Keyboard', 'RGB backlit keyboard with blue switches', 89.99, 15),
    ('HD Monitor', '24-inch Full HD LED monitor', 159.99, 10);

DROP TABLE IF EXISTS users;
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);

INSERT INTO users(email, password_hash) VALUES 
    ('alice@example.com', 'UGFzc3dvcmQx'), 
    ('bob@example.com', 'UGFzc3dvcmQx'),
    ('admin@example.com', 'UGFzc3dvcmQx');

DROP TABLE IF EXISTS orders;
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    total_amount REAL NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);
```

Die Passwörter sind **base64-kodiert** (nur zu Demo-Zwecken). Nutzer und Bestellungen sind relational verknüpft.
### Web API

Der Aufbau des Backends:
```
app/
├── main.py           # Hauptanwendung
├── db.py             # Datenbank-Interaktion
├── web_api.py        # Web-API-Endpunkte
```

**Implementierte Endpunkte:**
- `POST /login` — Benutzer-Login
- `POST /logout` — Benutzer abmelden
- `GET /products` — Alle Produkte anzeigen
- `POST /orders` — Bestellung erstellen (nur mit Authentifizierung)
- `GET /orders` — Bestellungen des Nutzers (nur mit Authentifizierung)
- `GET /orders/me` — Eigene Bestellungen (nur mit Authentifizierung)
- `PUT /admin/orders/{order_id}` — Status aktualisieren (nur Admin)
- `DELETE /admin/orders/{order_id}` — Bestellung löschen (nur Admin)    

---

## Geschäftsprozess & Camunda

Der eigentliche Geschäftsprozess wurde im **Camunda Modeler** erstellt und in der **Camunda Process Engine** ausgeführt. Die Web-API kann so auch komplett von Camunda aus (über REST) angesteuert werden.

### Grundlegender Ablauf

- Bestellung anlegen → Produkte prüfen → evtl. Nachbestellen → Verpacken → Versand anstossen (Nachricht) → Postprozess übernimmt
    
- Der **Post-Prozess** startet dabei nicht automatisch mit dem Hauptprozess, sondern wird erst durch eine **Message (z.B. `post_uebergeben`)** getriggert.
    
- Verschiedene Pools/Teilnehmer repräsentieren verschiedene Beteiligte wie Shop, Kunde, Lieferant, Post.
    

---

## Herausforderungen & Erkenntnisse

### 1. **External Task Worker & Threading**

- **Problem:** Zunächst wurde der Camunda `ExternalTaskWorker` mit nur einer Funktion (`subscribe()`) gestartet, was dazu führte, dass jeweils nur ein Task verarbeitet wurde.
- **Lösung:** Für jeden Service Task-Topic musste ein **eigener Worker in einem eigenen Thread** laufen, damit mehrere Tasks parallel abgearbeitet werden können. Am Ende waren es 10 Threads für 10 verschiedene Topics.
- **Lernpunkt:** Camunda External Task Worker blockieren standardmässig, d.h. ein Worker kann immer nur ein Topic bedienen.
### 2. **Pool-Konfiguration & Prozessstart**

- **Problem:** Beim Starten des Prozesses wurden plötzlich mehrere Pools (z.B. „Shop“ und „Post“) unabhängig voneinander gestartet, auch ohne zugehörige Bestellung.
- **Ursache:** Die Pools/Prozesse waren als **`startable`** in der Tasklist konfiguriert.
- **Lösung:** Die Pools wurden auf **`Non-Startable`** gesetzt, sodass sie nur durch Nachrichten aus dem Hauptprozess oder einen gezielten API-Aufruf starten.
- **Lernpunkt:** Pools dürfen **nicht** als „startable in tasklist“ markiert sein, wenn sie _nur_ durch Nachrichten/Ereignisse getriggert werden sollen.
    
### 3. **Post-Prozess: Kein Job sichtbar**

- **Problem:** Nach Auslösen der „Ware versenden“-Nachricht wurde der Post-Prozess zwar instanziiert, aber es erschien **kein Job** im Cockpit.
- **Ursache:** Im Post-Prozess war der erste Schritt ein **Manual Task** (statt Service Task), daher wurde **kein Camunda-Job** erzeugt.
- **Lösung:** Den Task auf **Service Task (camunda:type="external")** umstellen und ein Topic vergeben, damit ein Job entsteht und ein Worker diesen verarbeiten kann.
- **Lernpunkt:** Nur Service Tasks mit „External“ Implementation erzeugen Camunda Jobs, die von Workern übernommen werden können.
    

### 4. **Message Events & Namensgebung**

- **Problem:** Nachrichten zum Starten eines Prozesses wurden nicht korrekt verarbeitet (Fehlermeldung: „Cannot correlate message...“).
- **Ursache:** Der Message-Name im Aufruf (z.B. `kunden_uebergeben`) stimmte nicht exakt mit dem im BPMN-Modell (`post_uebergeben`) überein.
- **Lösung:** Die Namen **exakt** im BPMN und beim Senden/Empfangen anpassen.
- **Lernpunkt:** Message-Namen müssen 1:1 übereinstimmen (inkl. Gross-/Kleinschreibung), damit Camunda Nachrichten korrekt korreliert.

### 5. **Variablen-Kontext**

- **Problem:** Prozess-Variablen wie `user_id` oder `product_id` wurden nicht gefunden oder falsch gesetzt.
- **Lösung:** Sicherstellen, dass alle benötigten Variablen **rechtzeitig** im richtigen Kontext übergeben und im Prozessverlauf gesetzt werden.
- **Lernpunkt:** Variablen in Camunda sind immer an eine Prozessinstanz oder einen Task gebunden und müssen explizit übergeben werden.
    

### 6. **Fehlersuche & Debugging in Camunda**

- **Cockpit** ist das wichtigste Tool zur Prozessüberwachung:
    - Dort sieht man, wo Tokens steckenbleiben, welche Events ausgeführt wurden und ob Jobs erzeugt werden.
- **XML direkt kontrollieren:** Manchmal stimmen grafische Einstellungen, aber im XML fehlen Implementation/Topic bei Tasks oder Nachrichten-Namen sind falsch.
    

---

## Zusammenfassung & Best Practices

- **Backend und Prozesse trennen:** API und BPMN sollten klar abgegrenzt sein; das BPMN-Modell steuert den Geschäftsablauf, das Backend verarbeitet die "Arbeit".
- **Camunda External Tasks:** Nur Service Tasks mit „External“ erzeugen Jobs für Worker.
- **Worker pro Topic:** Jeder Worker sollte ein eigenes Topic bedienen, sonst gibt es Bottlenecks.
- **Konsistente Namensgebung:** Nachrichten müssen in BPMN und API-Aufrufen **identisch** heissen.
- **Cockpit für Fehleranalyse nutzen**: Bleibt ein Token stehen, stimmt meist die Modellierung, Topic oder der Nachricht-Name nicht.
- **Prozesse nicht als startable markieren**, wenn sie nur durch Nachrichten gestartet werden sollen.
    

---
## Persönliches Fazit

Das Projekt hat eindrucksvoll gezeigt, wie wichtig es ist, BPMN-Prozesse, Nachrichtenflüsse und technische Implementierung konsequent aufeinander abzustimmen. Insbesondere das Zusammenspiel von Nachrichten, External Tasks und den jeweiligen Worker-Prozessen ist entscheidend für eine funktionierende Prozessautomatisierung.

Die Arbeit mit Camunda als Prozessengine war für uns insgesamt eher ernüchternd. Trotz der theoretisch sehr klaren BPMN-Logik und der grossen Flexibilität im Design war die praktische Umsetzung mit Camunda deutlich komplexer und zeitintensiver als erwartet.

Viele Probleme – etwa beim Zusammenspiel von Nachrichten, External Tasks, Worker-Implementierung oder Variablenhandling – kosteten viel Zeit und Nerven. Besonders frustrierend war, dass viele Fehlerquellen nicht offensichtlich waren und sich durch spärliche oder teilweise veraltete Ressourcen und Dokumentationen im Netz nur schwer lösen liessen. Die Fehlermeldungen von Camunda sind oft wenig sprechend und erfordern viel Trial-and-Error sowie tiefes Debugging im Cockpit und BPMN-XML.

Auch der Community-Support war weniger hilfreich als erhofft. Viele Lösungen mussten wir letztlich selbst durch systematisches Probieren, intensive Recherche und eigenständiges Debugging erarbeiten. 
  
Camunda bietet zwar viele Möglichkeiten, die tatsächliche Entwicklung und Fehlersuche kann aber schnell sehr mühsam werden. Ohne vertieftes Vorwissen und ausreichend Zeit für Testen und Debugging stösst man rasch an Grenzen – gerade bei komplexeren, mehrstufigen Prozessen. Für kleine Prototypen ist Camunda interessant, für produktive, grössere Projekte aber aus unserer Sicht nur mit sehr viel Einarbeitung und Geduld zu empfehlen.
