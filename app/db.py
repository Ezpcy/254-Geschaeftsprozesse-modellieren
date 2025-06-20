import base64
import sqlite3

class Db:
    def __init__(self, db_path: str = "../digitec.db"):
        self.db_path = db_path

    def get_all_products(self):
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute("SELECT * FROM products").fetchall()

    def get_product(self, product_id):
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()

    def create_product(self, name, description, price, stock):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO products (name, description, price, stock)
                VALUES (?, ?, ?, ?)
            """, (name, description, price, stock))
            conn.commit()

    def update_product(self, product_id, name, description, price, stock):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE products SET name = ?, description = ?, price = ?, stock = ?
                WHERE id = ?
            """, (name, description, price, stock, product_id))
            conn.commit()

    def delete_product(self, product_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()

    def insert_order(self, user_id, product_id, quantity):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT price, stock FROM products WHERE id = ?", (product_id,))
            result = cursor.fetchone()
            if result is None:
                return "Product not found."

            price, stock = result
            if stock < quantity:
                return "Not enough stock."
            if quantity == 0:
                return "Cannot order 0 items."

            total = price * quantity
            cursor.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (quantity, product_id))
            cursor.execute("""
                INSERT INTO orders (user_id, product_id, quantity, total_amount)
                VALUES (?, ?, ?, ?)
            """, (user_id, product_id, quantity, total))
            conn.commit()
            return "Order inserted."

    def get_orders_by_user(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute("""
                SELECT orders.id, users.email, product_id, quantity, total_amount, status, created_at
                FROM orders
                JOIN users ON users.id = orders.user_id
                WHERE user_id = ?
            """, (user_id,)).fetchall()

    def get_orders_with_user_info(self):
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute("""
                SELECT
                    orders.id,
                    users.email,
                    orders.product_id,
                    orders.quantity,
                    orders.total_amount,
                    orders.status,
                    orders.created_at
                FROM orders
                JOIN users ON users.id = orders.user_id
                ORDER BY orders.created_at DESC
            """).fetchall()

    def validate_user(self, email: str, password: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            if not row:
                return False
            expected_hash = row[0]
            try:
                decoded = base64.b64decode(expected_hash.encode()).decode()
            except Exception:
                return False
            return decoded == password

    def get_user_id_by_email(self, email: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            if not row:
                raise ValueError("User not found")
            return row[0]




