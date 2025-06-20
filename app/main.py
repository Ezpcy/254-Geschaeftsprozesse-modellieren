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
    "sleepSeconds": 30
}

def handle_bestellung_lager(task: ExternalTask) -> TaskResult:
    product_id = task.get_variable("product_id")
    quantity = task.get_variable("quantity")

    if product_id is None or quantity is None:
        return task.failure("Missing input", "Variables are missing", 0, 0)

    product_id = int(product_id)
    quantity = int(quantity)


    print(f"Bestelle {quantity} Stück von Produkt {product_id}")
    return task.complete()

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

def handle_pruefen(task: ExternalTask) -> TaskResult:
    product_id = task.get_variable("product_id")
    quantity = task.get_variable("quantity")

    if product_id is None or quantity is None:
        return task.failure("Missing input", "Variables are missing", 0, 0)

    product_id = int(product_id)
    quantity = int(quantity)

    result = db.get_product(product_id)
    if not result or result[4] < quantity:
        send_message("lager_bestellen", {
            "product_id": product_id,
            "quantity": quantity
        })
        return task.complete()

    print(f"Genügend Lager für Produkt {product_id}")
    return task.complete()

def start_worker():
    worker = ExternalTaskWorker(worker_id="1", config=default_config)
    worker.subscribe("bestellung_pruefen", handle_pruefen)
    worker.subscribe("bestellung_lager", handle_bestellung_lager)

if __name__ == "__main__":
    threading.Thread(target=start_worker, daemon=True).start()
    uvicorn.run(get_app(), host="127.0.0.1", port=8000, reload=True)


