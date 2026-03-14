import sqlite3

def get_db_tables():
    conn = sqlite3.connect('/root/home.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables


def get_widget_data(table_name, column_name, calculation):
    try:
        conn = sqlite3.connect('/root/home.db')
        cursor = conn.cursor()

        ops = {
            "last": f"SELECT {column_name} FROM {table_name} ORDER BY Tim DESC LIMIT 1",
            "min": f"SELECT MIN({column_name}) FROM {table_name}",
            "max": f"SELECT MAX({column_name}) FROM {table_name}",
            "avg": f"SELECT AVG({column_name}) FROM {table_name}"
        }

        query = ops.get(calculation)
        cursor.execute(query)
        result = cursor.fetchone()
        conn.close()

        if result and result[0] is not None:
            return round(result[0], 2) if isinstance(result[0], float) else result[0]
        return "--"
    except Exception as e:
        print(f"DB Error: {e}")
        return "Err"