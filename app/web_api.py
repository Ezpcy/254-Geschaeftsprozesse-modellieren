from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from db import Db
from itsdangerous import URLSafeSerializer
import sqlite3

SECRET_KEY = "BiggieBalls"
signer = URLSafeSerializer(SECRET_KEY, salt="session")

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    stock: int

class ProductUpdate(ProductCreate):
    id: int

class OrderCreate(BaseModel):
    product_id: int
    quantity: int

class OrderUpdate(BaseModel):
    status: str

security = HTTPBasic()
db = Db()

ADMIN_EMAILS = ["admin@example.com"]

def basic_auth(credentials: HTTPBasicCredentials = Depends(security)):
    email = credentials.username
    password = credentials.password
    if not db.validate_user(email, password):
        raise HTTPException(status_code=401, detail="Invalid credentials", headers={"WWW-Authenticate": "Basic"})
    return email

def session_auth(request: Request):
    session_cookie = request.cookies.get("session")
    if not session_cookie:
        raise HTTPException(status_code=401, detail="Not authenticated (missing cookie)")
    try:
        user_email = signer.loads(session_cookie)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid session")
    return user_email

def admin_auth(email: str = Depends(session_auth)):
    if email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admins only")
    return email

class OnlineShopAPI:
    def __init__(self):
        self.app = FastAPI()

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Allow all domains (for testing)
            allow_credentials=True,
            allow_methods=["*"],  # Allow all HTTP methods
            allow_headers=["*"],  # Allow all headers
        )

        self.db = db
        self.setup_routes()

    def setup_routes(self):
        @self.app.post("/login")
        def login(response: Response, credentials: HTTPBasicCredentials = Depends(security)):
            if not self.db.validate_user(credentials.username, credentials.password):
                raise HTTPException(status_code=401, detail="Invalid credentials")

            signed = signer.dumps(credentials.username)
            response.set_cookie("session", signed, httponly=True)
            return {"message": "Login successful"}

        @self.app.post("/logout")
        def logout(response: Response):
            response.delete_cookie("session")
            return {"message": "Logged out"}

        @self.app.get("/products")
        def list_products():
            return self.db.get_all_products()

        @self.app.post("/orders")
        def create_order(order: OrderCreate, email: str = Depends(session_auth)):
            try:
                user_id = self.db.get_user_id_by_email(email)
            except ValueError:
                raise HTTPException(status_code=400, detail="User not found")

            result = self.db.insert_order(user_id, order.product_id, order.quantity)
            if "inserted" not in result.lower():
                raise HTTPException(status_code=400, detail=result)
            return {"message": result}

        @self.app.get("/orders")
        def list_orders(email: str = Depends(session_auth)):
            try:
                user_id = self.db.get_user_id_by_email(email)
            except ValueError:
                raise HTTPException(status_code=400, detail="User not found")
            return self.db.get_orders_by_user(user_id)

        @self.app.get("/orders/me")
        def list_my_orders(email: str = Depends(session_auth)):
            try:
                user_id = self.db.get_user_id_by_email(email)
            except ValueError:
                raise HTTPException(status_code=400, detail="User not found")
            return self.db.get_orders_by_user(user_id)

        @self.app.put("/admin/orders/{order_id}")
        def update_order_status(order_id: int, update: OrderUpdate, email: str = Depends(admin_auth)):
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (update.status, order_id))
                conn.commit()
            return {"message": f"Order {order_id} updated to status '{update.status}'"}

        @self.app.delete("/admin/orders/{order_id}")
        def delete_order(order_id: int, email: str = Depends(admin_auth)):
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
                conn.commit()
            return {"message": f"Order {order_id} deleted"}


def get_app():
    api = OnlineShopAPI()
    return api.app
