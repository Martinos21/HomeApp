import itertools
from tools.dbTools import get_db_tables
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import random
import socket
import uuid
from src.tools.hotspot import start_hotspot, stop_hotspot
from src.tools.dbTools import get_widget_data, get_historical_data
import requests
import os
import json

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = "smart_home_secret"
SETTINGS_FILE = 'settings.json'
widgets = []
widget_id_counter = itertools.count(1)

def get_config():
    """Pomocná funkce pro načtení nastavení ze souboru."""
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

# Get Raspberry Pi IP and MAC
def get_network_info():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    mac_address = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) for i in range(0, 48, 8)][::-1])
    return {"ip": ip_address, "mac": mac_address}

@app.route('/')
def home():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    db_tables = get_db_tables()
    return render_template('dashboard.html', widgets=widgets, db_tables=db_tables)


@app.route('/add_widget', methods=['POST'])
def add_widget():
    data = request.get_json()
    new_id = f'widget-{next(widget_id_counter)}'

    new_widget = {
        'id': new_id,
        'title': data.get('title'),
        'table': data.get('type'),  # e.g., 'living_room'
        'sensor': data.get('sensor'),  # e.g., 'temp', 'humidity'
        'calc': data.get('calc')  # e.g., 'avg'
    }
    widgets.append(new_widget)
    return jsonify({'success': True, 'id': new_id})


@app.route('/api/widget_data/<widget_id>')
def widget_data(widget_id):
    widget = next((w for w in widgets if w['id'] == widget_id), None)
    if not widget:
        return jsonify({'error': 'Not found'}), 404

    data = get_widget_data(widget['table'], widget['sensor'], widget['calc'])
    return jsonify(data) # Returns {"value": 22.5, "timestamp": "2026-03-14 20:50:00"}


@app.route('/api/widget_history/<widget_id>')
def widget_history(widget_id):
    # Find the widget configuration
    widget = next((w for w in widgets if w['id'] == widget_id), None)
    if not widget:
        return jsonify({'error': 'Not found'}), 404

    range_type = request.args.get('range')
    start_date = request.args.get('start')
    end_date = request.args.get('end')

    data = get_historical_data(
        table_name=widget['table'],
        column_name=widget['sensor'],
        range_type=range_type,
        start_date=start_date,
        end_date=end_date
    )

    return jsonify(data)

@app.route('/delete_widget', methods=['POST'])
def delete_widget():
        data = request.get_json()
        widget_id_to_delete = data.get('id')

        global widgets
        initial_count = len(widgets)
        widgets = [w for w in widgets if w.get('id') != widget_id_to_delete]

        if len(widgets) < initial_count:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Widget not found'}), 404

@app.route('/devices')
def devices():
    return render_template('devices.html')

@app.route('/settings')
def settings():
    config = get_config()
    return render_template('settings.html', config=config)

@app.route('/api/save_settings', methods=['POST'])
def save_settings():
    try:
        new_config = request.get_json()
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(new_config, f)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/get_config')
def get_config_api():
    return jsonify(get_config())

if __name__ == '__main__':
    #stop_hotspot()
    start_hotspot(ssid="test", password="test1234")
    app.run(host='0.0.0.0', port=8000, debug=True)

