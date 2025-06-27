from camunda.external_task.external_task import ExternalTask, TaskResult
from camunda.external_task.external_task_worker import ExternalTaskWorker
from db import Db
from requests import post
from web_api import get_app
import threading
import uvicorn

db = Db()

default_config = {
    "maxTasks": 1,
    "lockDuration": 10000,
    "asyncResponseTimeout": 5000,
    "retries": 3,
    "retryTimeout": 5000,
    "sleepSeconds": 2
}

def login_angaben(task: ExternalTask) -> TaskResult:
    print("Login Angaben task started")
    email = input("Bitte geben Sie Ihre E-Mail-Adresse ein: ")
    password = input("Bitte geben Sie Ihr Passwort ein: ")
    
    if not email or not password:
        return task.complete("Error", "No login details provided")

    return task.complete({"email": email, "password": password})

def login(task: ExternalTask) -> TaskResult:
    print("Login task started")
    email = task.get_variable("email")
    password = task.get_variable("password")
    if (email == None) and (password == None):
        return task.complete("Error", "No login details provided")

    if db.validate_user(str(email), str(password)):
        user_id = db.get_user_id_by_email(str(email))
        return task.complete({"validated": True, "user_id": user_id})
    else:
        print("Login Daten falsch")
        return task.complete("Not authorized", "User Not authorized")


def produkte_suchen(task: ExternalTask) -> TaskResult:
    print("Produkte suchen task started")
    produkte = db.get_all_products()
    print(f"Folgende Produkte gefunden: {produkte}")
    bestellen= int(input("Welches Produkt möchten Sie bestellen? (ID eingeben): "))
    quantity = int(input("Wie viele Stück möchten Sie bestellen? (Anzahl eingeben): "))
    if not db.get_product(bestellen):
        print("Produkt nicht gefunden")
        return task.complete({"gefunden": False, "message": "Produkt nicht gefunden"})
    if db.get_product(bestellen)[4] < quantity:
        print("Nicht genügend Lagerbestand")
        return task.complete({"gefunden": False, "message": "Nicht genügend Lagerbestand"})
    print(f"Bestelle {quantity} Stück von Produkt {bestellen}")
    return task.complete({"product_id": bestellen, "quantity": quantity, "gefunden": True})

def bestellung_prüfen(task: ExternalTask) -> TaskResult:
    print("Bestellung prüfen task started")
    product_id = task.get_variable("product_id")
    user_id = db.get_user_id_by_email(str(task.get_variable("email")))
    quantity = task.get_variable("quantity")
    product_name = db.get_product(product_id)[1]

    print(f"Du bestellst {quantity} Stück von {product_name} (ID: {product_id})")
    submit = input("Möchtest du die Bestellung abschließen? (ja/nein): ").strip().lower()
    if submit == "ja":
        print("Bestellung erfolgreich!")
        db.insert_order(
            user_id,
            product_id,
            quantity
        )
        # Start the OnlineShop process
        send_message("bestellung_abgeschlossen", {
            "user_id": user_id,
            "product_id": product_id,
            "quantity": quantity
        })
        return task.complete({"bestellung_abgeschlossen": True})
    else:
        return task.complete({"bestellung_abgeschlossen": False})

def handle_bestellung_lager(task: ExternalTask) -> TaskResult:
    print("Handle Bestellung Lager task started")
    product_id = task.get_variable("product_id")
    quantity = task.get_variable("quantity")

    if product_id is None or quantity is None:
        return task.failure("Missing input", "Variables are missing", 0, 0)

    quantity = int(quantity)


    print(f"Bestelle {quantity} Stück von Produkt {product_id}")
    return task.complete()

def status_versand(task: ExternalTask) -> TaskResult:
    print("Status Versand task started")
    user_id = task.get_variable("user_id")
    order_id = db.get_orders_by_user(user_id)[0][0]
    status = "Versendet"

    if order_id is None or status is None:
        return task.failure("Missing input", "Order ID or status is missing", 0, 0)

    print(f"Bestellung {order_id} hat den Status: {status}")
    db.update_order_status(order_id, status)
    send_message("ware_versenden", {
        "user_id": task.get_variable("user_id"),
        "product_id":  task.get_variable("product_id"),
        "quantity": task.get_variable("quantity")
    })
    return task.complete({"order_id": order_id, "status": status})

def handle_pruefen(task: ExternalTask) -> TaskResult:
    print("Handle Prüfen task started")
    product_id = task.get_variable("product_id")
    quantity = task.get_variable("quantity")
    print(f"Prüfe Lagerbestand für Produkt {product_id} mit Menge {quantity}")
    result = db.get_product(product_id)
    if result and result[4] >= quantity:
        print("Lagerbestand ausreichend, Bestellung kann bearbeitet werden.")
        return task.complete({"genug_lager": True})
    else:
        print("Lagerbestand nicht ausreichend, Ware wird vom Lieferanten bestellt.")
        return task.complete({"genug_lager": False})

def post_starten(task: ExternalTask)-> TaskResult:
    print("Post starten task started")
    return task.complete({"message": "Post gestartet"})

def kunden_uebergeben(task: ExternalTask) -> TaskResult:
    print("Kunden übergeben task started")
    user_id = task.get_variable("user_id")
    product_id = task.get_variable("product_id")
    quantity = task.get_variable("quantity")

    if user_id is None or product_id is None or quantity is None:
        return task.failure("Missing input", "User ID, Product ID or Quantity is missing", 0, 0)

    print(f"Übergebe Kunde {user_id} Produkt {product_id} mit Menge {quantity}")
    send_message("kunden_uebergeben", {
        "user_id": user_id,
        "product_id": product_id,
        "quantity": quantity
    })
    send_message("post_abschluss", {
        "user_id": user_id,
        "product_id": product_id,
        "quantity": quantity
    })
    return task.complete({"user_id": user_id, "product_id": product_id, "quantity": quantity})

def status_abgeschlossen(task: ExternalTask) -> TaskResult:
    print("Status abgeschlossen task started")
    order_id = task.get_variable("order_id")
    status = "Abgeschlossen"

    if order_id is None or status is None:
        return task.failure("Missing input", "Order ID or status is missing", 0, 0)

    print(f"Bestellung {order_id} hat den Status: {status}")
    db.update_order_status(order_id, status)
    return task.complete({"order_id": order_id, "status": status})

def send_message(name: str, variables: dict):
    url = "http://localhost:8080/engine-rest/message"
    payload = {
        "messageName": name,
        "processVariables": {
            key: {"value": value, "type": "String" if isinstance(value, str) else "Integer"}
            for key, value in variables.items()
        }
    }
    post(url, json=payload)

#def start_worker():
    #worker = ExternalTaskWorker(worker_id="1", config=default_config).subscribe("handle_pruefen", handle_pruefen).subscribe("handle_bestellung_lager", handle_bestellung_lager).subscribe("login", login).subscribe("produkte_suchen", produkte_suchen).subscribe("bestellung_prüfen", bestellung_prüfen)

if __name__ == "__main__":
    #threading.Thread(target=start_worker, daemon=True).start()
    #uvicorn.run(get_app(), host="127.0.0.1", port=8000, reload=True)
    
    # ExternalTaskWorker(worker_id="1", config=default_config).subscribe("login", login)
    # ExternalTaskWorker(worker_id="2", config=default_config).subscribe("produkte_suchen", produkte_suchen)
    # ExternalTaskWorker(worker_id="2", config=default_config).subscribe("handle_bestellung_lager", handle_bestellung_lager)
    # ExternalTaskWorker(worker_id="3", config=default_config).subscribe("bestellung_prüfen", bestellung_prüfen)
    # ExternalTaskWorker(worker_id="4", config=default_config).subscribe("handle_pruefen", handle_pruefen)
    # ExternalTaskWorker(worker_id="5", config=default_config).start()

    worker1 = threading.Thread(target=lambda: ExternalTaskWorker(worker_id="1", config=default_config).subscribe("login", login).start(), daemon=False)
    worker2 = threading.Thread(target=lambda: ExternalTaskWorker(worker_id="1", config=default_config).subscribe("produkte_suchen", produkte_suchen).start(), daemon=False)
    worker3 = threading.Thread(target=lambda: ExternalTaskWorker(worker_id="1", config=default_config).subscribe("handle_bestellung_lager", handle_bestellung_lager).start(), daemon=False)
    worker4 = threading.Thread(target=lambda: ExternalTaskWorker(worker_id="1", config=default_config).subscribe("bestellung_prüfen", bestellung_prüfen).start(), daemon=False)
    worker5 = threading.Thread(target=lambda: ExternalTaskWorker(worker_id="1", config=default_config).subscribe("handle_pruefen", handle_pruefen).start(), daemon=False)
    worker6 = threading.Thread(target=lambda: ExternalTaskWorker(worker_id="1", config=default_config).subscribe("login_angaben", login_angaben).start(), daemon=False)
    worker7 = threading.Thread(target=lambda: ExternalTaskWorker(worker_id="1", config=default_config).subscribe("status_versand", status_versand).start(), daemon=False)
    worker8 = threading.Thread(target=lambda: ExternalTaskWorker(worker_id="1", config=default_config).subscribe("status_abgeschlossen", status_abgeschlossen).start(), daemon=False)
    worker9 = threading.Thread(target=lambda: ExternalTaskWorker(worker_id="1", config=default_config).subscribe("post_starten", post_starten).start(), daemon=False)
    worker10 = threading.Thread(target=lambda: ExternalTaskWorker(worker_id="1", config=default_config).subscribe("kunden_uebergeben", kunden_uebergeben).start(), daemon=False)
    worker1.start()
    worker2.start()
    worker3.start()
    worker4.start()
    worker5.start()
    worker6.start()
    worker7.start()
    worker8.start()
    worker9.start()
    worker10.start()

