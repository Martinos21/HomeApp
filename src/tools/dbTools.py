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

        # We fetch the value AND the timestamp (Tim)
        # Note: For min/max/avg, we usually want the latest timestamp in that table
        ops = {
            "last": f"SELECT {column_name}, Tim FROM {table_name} ORDER BY Tim DESC LIMIT 1",
            "min": f"SELECT MIN({column_name}), MAX(Tim) FROM {table_name}",
            "max": f"SELECT MAX({column_name}), MAX(Tim) FROM {table_name}",
            "avg": f"SELECT AVG({column_name}), MAX(Tim) FROM {table_name}"
        }

        query = ops.get(calculation)
        cursor.execute(query)
        result = cursor.fetchone()
        conn.close()

        if result and result[0] is not None:
            val = round(result[0], 2) if isinstance(result[0], float) else result[0]
            return {"value": val, "timestamp": result[1]}
        return {"value": "--", "timestamp": None}
    except Exception as e:
        print(f"DB Error: {e}")
        return {"value": "Err", "timestamp": None}


def get_historical_data(table_name, column_name, limit=20):
    try:
        conn = sqlite3.connect('/root/home.db')
        cursor = conn.cursor()
        # Fetch data ordered by time
        query = f"SELECT {column_name}, Tim FROM {table_name} ORDER BY Tim DESC LIMIT ?"
        cursor.execute(query, (limit,))
        results = cursor.fetchall()
        conn.close()

        if not results:
            return {"values": [], "labels": [], "latest_timestamp": None}

        # The first row in DESC order is the newest
        latest_ts = results[0][1]

        results.reverse()  # Reverse for left-to-right graphing
        return {
            "values": [row[0] for row in results],
            "labels": [row[1].split(' ')[1] for row in results],
            "latest_timestamp": latest_ts
        }
    except Exception as e:
        return {"values": [], "labels": [], "latest_timestamp": None}