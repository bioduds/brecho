\
import sqlite3
from contextlib import contextmanager

DB_PATH = "brecho.db"

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()

def init_db():
    with get_conn() as conn:
        c = conn.cursor()
        # Consignors
        c.execute("""
        CREATE TABLE IF NOT EXISTS consignors (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            whatsapp TEXT,
            email TEXT,
            pix_key TEXT,
            percent REAL DEFAULT 0.5,
            notes TEXT,
            active INTEGER DEFAULT 1
        );
        """)
        # Items
        c.execute("""
        CREATE TABLE IF NOT EXISTS items (
            sku TEXT PRIMARY KEY,
            consignor_id TEXT,
            acquisition_type TEXT,   -- consignação | doação | compra
            category TEXT,
            subcategory TEXT,
            brand TEXT,
            gender TEXT,
            size TEXT,
            fit TEXT,
            color TEXT,
            fabric TEXT,
            condition TEXT,
            flaws TEXT,
            bust REAL,
            waist REAL,
            length REAL,
            cost REAL DEFAULT 0,
            list_price REAL,
            markdown_stage INTEGER DEFAULT 0,
            acquired_at TEXT,
            listed_at TEXT,
            channel_listed TEXT,
            sold_at TEXT,
            sale_price REAL,
            channel_sold TEXT,
            days_on_hand INTEGER,
            photos_url TEXT,
            notes TEXT,
            active INTEGER DEFAULT 1,
            FOREIGN KEY(consignor_id) REFERENCES consignors(id)
        );
        """)
        # Sales
        c.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id TEXT PRIMARY KEY,
            date TEXT NOT NULL,
            sku TEXT NOT NULL,
            sale_price REAL NOT NULL,
            discount_value REAL DEFAULT 0,
            channel TEXT,
            customer_name TEXT,
            customer_whatsapp TEXT,
            payment_method TEXT,
            notes TEXT,
            consignor_id TEXT,
            FOREIGN KEY(sku) REFERENCES items(sku)
        );
        """)

def upsert(table: str, key_field: str, data: dict):
    keys = list(data.keys())
    placeholders = ",".join(["?"]*len(keys))
    columns = ",".join(keys)
    update_clause = ",".join([f"{k}=excluded.{k}" for k in keys if k != key_field])
    sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) "\
          f"ON CONFLICT({key_field}) DO UPDATE SET {update_clause};"
    with get_conn() as conn:
        conn.execute(sql, [data[k] for k in keys])

def delete(table: str, key_field: str, key_value: str):
    with get_conn() as conn:
        conn.execute(f"DELETE FROM {table} WHERE {key_field}=?", (key_value,))

def fetchall(sql: str, params=()):
    with get_conn() as conn:
        cur = conn.execute(sql, params)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
    return cols, rows
