"""ETL Load — Populate SQLite warehouse."""
import sqlite3, pandas as pd, os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'warehouse.db')

def get_conn():
    return sqlite3.connect(DB_PATH)

def load_table(conn, df, name):
    df.to_sql(name, conn, if_exists='replace', index=False)
    conn.execute("INSERT INTO etl_log (table_name, rows_loaded) VALUES (?, ?)", (name, len(df)))
    conn.commit()
    print(f"  Loaded {name}: {len(df):,} rows")

def create_schema(conn):
    conn.executescript("""
    DROP TABLE IF EXISTS etl_log;
    CREATE TABLE etl_log (table_name TEXT, rows_loaded INTEGER, loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
    """)

def load_all(tables_dict):
    conn = get_conn()
    create_schema(conn)
    for name, df in tables_dict.items():
        load_table(conn, df, name)
    print(f"\n  Warehouse: {DB_PATH}")
    conn.close()
