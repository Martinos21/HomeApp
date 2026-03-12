import sqlite3

def get_db_tables():
    conn = sqlite3.connect('home.db')
    cursor = conn.cursor()
    # Získáme názvy všech uživatelských tabulek
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables