import itertools
import sqlite3
import datetime
import os
import json

from flask import Flask, request, jsonify
from flask_cors import CORS
import paho.mqtt.publish as publish

from src.tools.dbTools import get_widget_data, get_historical_data
from src.tools.hotspot import start_hotspot
from src.tools.automation import automation_worker
import threading
import uuid

app = Flask(__name__)
CORS(app)

automations = []

SETTINGS_FILE = 'settings.json'
widgets = []
widget_id_counter = itertools.count(1)

def get_config():
    default_config = {
        "username": "Domácí uživatel",
        "email": "",
        "refresh": "30",
        "temp_unit": "c",
        "security": False
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return {**default_config, **json.load(f)}
        except:
            return default_config
    return default_config

# --- Senzorová data (příjem z M5Stack) ---

@app.route('/data', methods=['POST'])
def data():
    d = request.json
    tName = request.headers.get('Name')
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    values = (d.get('co2'), d.get('temp'), d.get('hum'), current_time)

    with sqlite3.connect('/root/home.db') as con:
        cur = con.cursor()
        cur.execute(f"CREATE TABLE IF NOT EXISTS {tName} (CO2 FLOAT, Temp FLOAT, Hum FLOAT, Tim TEXT)")
        cur.execute(f"INSERT INTO {tName} (CO2, Temp, Hum, Tim) VALUES (?, ?, ?, ?)", values)
        con.commit()
    return "OK"

# --- Widgety ---

@app.route('/api/widget/add', methods=['POST'])
def add_widget():
    data = request.get_json()
    new_id = f'widget-{next(widget_id_counter)}'
    widgets.append({
        'id': new_id,
        'title': data.get('title'),
        'table': data.get('type'),
        'sensor': data.get('sensor'),
        'calc': data.get('calc')
    })
    return jsonify({'success': True, 'id': new_id})

@app.route('/api/widget/delete', methods=['POST'])
def delete_widget():
    global widgets
    widget_id_to_delete = request.get_json().get('id')
    initial_count = len(widgets)
    widgets = [w for w in widgets if w.get('id') != widget_id_to_delete]
    if len(widgets) < initial_count:
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Widget not found'}), 404

@app.route('/api/widget/data/<widget_id>')
def widget_data(widget_id):
    widget = next((w for w in widgets if w['id'] == widget_id), None)
    if not widget:
        return jsonify({'error': 'Not found'}), 404
    data = get_widget_data(widget['table'], widget['sensor'], widget['calc'])
    return jsonify(data)

@app.route('/api/widget/history/<widget_id>')
def widget_history(widget_id):
    widget = next((w for w in widgets if w['id'] == widget_id), None)
    if not widget:
        return jsonify({'error': 'Not found'}), 404
    data = get_historical_data(
        table_name=widget['table'],
        column_name=widget['sensor'],
        range_type=request.args.get('range'),
        start_date=request.args.get('start'),
        end_date=request.args.get('end')
    )
    return jsonify(data)

# --- Relé ---

@app.route('/api/relay/<int:relay_id>/<string:action>', methods=['POST'])
def control_relay(relay_id, action):
    publish.single(f"relay/relay{relay_id}", action.lower(), hostname="10.42.0.1")
    return jsonify({"status": "sent", "relay": relay_id, "action": action})

# --- Nastavení ---

@app.route('/api/settings', methods=['GET'])
def get_settings():
    return jsonify(get_config())

@app.route('/api/settings', methods=['POST'])
def save_settings():
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(request.get_json(), f)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/automation/add', methods=['POST'])
def add_automation():
    d = request.get_json()
    d['id'] = str(uuid.uuid4())
    d['relay_state'] = 'OFF'
    automations.append(d)
    return jsonify({'success': True, 'id': d['id']})

@app.route('/api/automation/list', methods=['GET'])
def list_automations():
    return jsonify(automations)

@app.route('/api/automation/delete', methods=['POST'])
def delete_automation():
    global automations
    aid = request.get_json().get('id')
    automations = [a for a in automations if a['id'] != aid]
    return jsonify({'success': True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8070, debug=True)
    worker_thread = threading.Thread(target=automation_worker(automations), daemon=True)
    worker_thread.start()