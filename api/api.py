import sqlite3
from flask import Flask, request
import datetime
import paho.mqtt.publish as publish

from src.tools.hotspot import start_hotspot

app = Flask(__name__)

@app.route('/data', methods=['POST'])
def data():
    d = request.json
    tName = request.headers.get('Name')
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    co2 = d.get('co2')
    temp = d.get('temp')
    hum = d.get('hum')
    values = (co2, temp, hum, current_time)

    with sqlite3.connect('/root/home.db') as con:
        cur = con.cursor()
        cur.execute(f"CREATE TABLE IF NOT EXISTS {tName} (CO2 FLOAT, Temp FLOAT, Hum FLOAT, Tim TEXT)")
        cur.execute(f"INSERT INTO {tName} (CO2, Temp, Hum, Tim) VALUES (?, ?, ?, ?)", values)
        con.commit()
        print("Data has been written to the database.")
    return "OK"

@app.route('/mqtt', methods=['POST'])
def mqtt():
    d = request.json
    topic = d.get('topic')
    payload = d.get('payload')
    publish.single(topic, payload, hostname="localhost")

if __name__ == "__main__":
    # Run Flask server
    # start_hotspot(ssid="test", password="test1234")
    # con = sqlite3.connect('/root/home.db')
    app.run(host="0.0.0.0", port=8070, debug=True)