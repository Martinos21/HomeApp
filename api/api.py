import sqlite3
from flask import Flask, request

app = Flask(__name__)

@app.route('/data', methods=['POST'])
def data():
    d = request.json
    for key, value in d.items():
        cur = con.cursor()
        cur.execute(f"CREATE TABLE IF NOT EXISTS {key} (value)")
        con.commit()
        cur.execute(f"INSERT INTO {key} VALUES ({value})")
        con.commit()
        cur.close()
    print(d)
    return "OK"


if __name__ == "__main__":
    # Run Flask server
    con = sqlite3.connect('home.db')
    app.run(host="0.0.0.0", port=8070)