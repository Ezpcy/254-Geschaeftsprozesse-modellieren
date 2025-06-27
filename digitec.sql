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

