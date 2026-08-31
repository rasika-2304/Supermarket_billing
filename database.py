import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "supermarket.db")
RECEIPT_DIR = os.path.join(DATA_DIR, "receipts")


class Database:
    def __init__(self, path=DB_PATH):
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(RECEIPT_DIR, exist_ok=True)
        self.path = path

    def connect(self):
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        return con

    def initialize(self):
        with self.connect() as con:
            con.executescript("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                category TEXT DEFAULT '',
                price REAL NOT NULL CHECK(price >= 0),
                stock INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
                tax REAL NOT NULL DEFAULT 0 CHECK(tax >= 0),
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bill_no TEXT UNIQUE NOT NULL,
                subtotal REAL NOT NULL,
                discount REAL NOT NULL DEFAULT 0,
                tax REAL NOT NULL DEFAULT 0,
                total REAL NOT NULL,
                paid REAL NOT NULL DEFAULT 0,
                change_amount REAL NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS bill_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bill_id INTEGER NOT NULL,
                product_id INTEGER,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                qty INTEGER NOT NULL,
                price REAL NOT NULL,
                tax REAL NOT NULL,
                line_total REAL NOT NULL,
                FOREIGN KEY(bill_id) REFERENCES bills(id) ON DELETE CASCADE,
                FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE SET NULL
            );
            """)
            if con.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
                sample = [
                    ("1001","Rice 5kg","Groceries",420,50,5),
                    ("1002","Sugar 1kg","Groceries",55,100,5),
                    ("1003","Milk 1L","Dairy",62,80,0),
                    ("1004","Bread","Bakery",45,60,0),
                    ("1005","Cooking Oil 1L","Groceries",155,40,5),
                    ("1006","Shampoo","Personal Care",120,30,12),
                    ("1007","Biscuits","Snacks",30,120,5),
                ]
                con.executemany(
                    "INSERT INTO products(code,name,category,price,stock,tax,created_at) VALUES(?,?,?,?,?,?,?)",
                    [x + (datetime.now().isoformat(timespec="seconds"),) for x in sample]
                )

    def list_products(self, search=""):
        with self.connect() as con:
            if search.strip():
                q = "%" + search.strip() + "%"
                return con.execute(
                    "SELECT * FROM products WHERE code LIKE ? OR name LIKE ? OR category LIKE ? ORDER BY name",
                    (q,q,q)).fetchall()
            return con.execute("SELECT * FROM products ORDER BY name").fetchall()

    def get_product(self, code):
        with self.connect() as con:
            return con.execute("SELECT * FROM products WHERE code=?", (code,)).fetchone()

    def add_product(self, code, name, category, price, stock, tax):
        with self.connect() as con:
            con.execute(
                "INSERT INTO products(code,name,category,price,stock,tax,created_at) VALUES(?,?,?,?,?,?,?)",
                (code,name,category,price,stock,tax,datetime.now().isoformat(timespec="seconds")))

    def update_product(self, pid, code, name, category, price, stock, tax):
        with self.connect() as con:
            con.execute(
                "UPDATE products SET code=?,name=?,category=?,price=?,stock=?,tax=? WHERE id=?",
                (code,name,category,price,stock,tax,pid))

    def delete_product(self, pid):
        with self.connect() as con:
            con.execute("DELETE FROM products WHERE id=?", (pid,))

    def create_bill(self, cart, subtotal, discount, tax, total, paid):
        bill_no = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
        now = datetime.now().isoformat(timespec="seconds")
        change = paid - total
        with self.connect() as con:
            cur = con.execute(
                "INSERT INTO bills(bill_no,subtotal,discount,tax,total,paid,change_amount,created_at) VALUES(?,?,?,?,?,?,?,?)",
                (bill_no,subtotal,discount,tax,total,paid,change,now))
            bid = cur.lastrowid
            for x in cart:
                con.execute(
                    "INSERT INTO bill_items(bill_id,product_id,code,name,qty,price,tax,line_total) VALUES(?,?,?,?,?,?,?,?)",
                    (bid,x["id"],x["code"],x["name"],x["qty"],x["price"],x["tax"],x["line_total"]))
                con.execute("UPDATE products SET stock=stock-? WHERE id=?", (x["qty"],x["id"]))
        return bill_no

    def list_bills(self):
        with self.connect() as con:
            return con.execute("SELECT * FROM bills ORDER BY id DESC").fetchall()

    def get_bill(self, bill_no):
        with self.connect() as con:
            bill = con.execute("SELECT * FROM bills WHERE bill_no=?", (bill_no,)).fetchone()
            if not bill:
                return None, []
            items = con.execute("SELECT * FROM bill_items WHERE bill_id=? ORDER BY id", (bill["id"],)).fetchall()
            return bill, items

    def dashboard(self):
        with self.connect() as con:
            return (
                con.execute("SELECT COUNT(*) FROM products").fetchone()[0],
                con.execute("SELECT COALESCE(SUM(stock),0) FROM products").fetchone()[0],
                con.execute("SELECT COUNT(*) FROM bills").fetchone()[0],
                con.execute("SELECT COALESCE(SUM(total),0) FROM bills").fetchone()[0]
            )
