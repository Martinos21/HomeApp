import sqlite3
from datetime import timedelta, datetime


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

def get_historical_data(table_name, column_name, range_type=None, start_date=None, end_date=None):
    try:
        conn = sqlite3.connect('/root/home.db')
        cursor = conn.cursor()

        query = f"SELECT {column_name}, Tim FROM {table_name}"
        params = []
        where_clauses = []

        if range_type:
            now = datetime.now()
            if range_type == 'week':
                delta = timedelta(weeks=1)
            elif range_type == 'month':
                delta = timedelta(days=30)
            elif range_type == '3months':
                delta = timedelta(days=90)
            elif range_type == 'year':
                delta = timedelta(days=365)
            else:
                delta = None

            if delta:
                start_ts = (now - delta).strftime('%Y-%m-%d %H:%M:%S')
                where_clauses.append("Tim >= ?")
                params.append(start_ts)

        elif start_date:
            where_clauses.append("Tim >= ?")
            params.append(start_date)
            if end_date:
                where_clauses.append("Tim <= ?")
                params.append(end_date)

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        query += " ORDER BY Tim DESC"

        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()

        if not results:
            return {"values": [], "labels": [], "latest_timestamp": None}

        latest_ts = results[0][1]
        results.reverse()

        return {
            "values": [row[0] for row in results],
            "labels": [row[1].split(' ')[1] if ' ' in row[1] else row[1] for row in results],
            "latest_timestamp": latest_ts
        }
    except Exception as e:
        print(f"Error: {e}")
        return {"values": [], "labels": [], "latest_timestamp": None}