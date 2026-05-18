import itertools
import sqlite3
import datetime
import os
import re
import json
import logging
import threading
import uuid
import time

from flask import Flask, request, jsonify
from flask_cors import CORS
import paho.mqtt.publish as publish

from src.tools.dbTools import get_widget_data, get_historical_data
from src.tools.hotspot import start_hotspot
from src.tools.automation import automation_worker

app = Flask(__name__)
CORS(app, origins=re.compile(r"http://(10\.42\.0|192\.168\.\d+)\.\d+.*"))

# ===== LOGGING =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler('api.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

automations = []
SETTINGS_FILE = 'settings.json'
WIDGETS_FILE = 'widgets.json'

TABLE_NAME_RE = re.compile(r'^[A-Za-z0-9_]{1,64}$')

def is_valid_table_name(name: str) -> bool:
    return bool(name and TABLE_NAME_RE.match(name))

def load_widgets() -> list:
    """Načte widgety z JSON souboru při startu aplikace."""
    if os.path.exists(WIDGETS_FILE):
        try:
            with open(WIDGETS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Nepodařilo se načíst widgets.json: {e}")
    return []

def save_widgets() -> None:
    """Uloží aktuální widgety do JSON souboru."""
    try:
        with open(WIDGETS_FILE, 'w') as f:
            json.dump(widgets, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Nepodařilo se uložit widgets.json: {e}")

widgets = load_widgets()
_max_id = max(
    (int(w['id'].split('-')[1]) for w in widgets if w.get('id', '').startswith('widget-')),
    default=0
)
widget_id_counter = itertools.count(_max_id + 1)

_request_counts = {}
_request_lock = threading.Lock()
RATE_LIMIT = 60
RATE_WINDOW = 60

def is_rate_limited(ip: str) -> bool:
    now = time.time()
    with _request_lock:
        counts = _request_counts.get(ip, [])
        counts = [t for t in counts if now - t < RATE_WINDOW]
        counts.append(now)
        _request_counts[ip] = counts
        return len(counts) > RATE_LIMIT


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
        except Exception as e:
            logger.warning(f"Nepodařilo se načíst settings.json: {e}")
            return default_config
    return default_config


@app.route('/data', methods=['POST'])
def data():
    d = request.json
    tName = request.headers.get('Name')
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if not is_valid_table_name(tName):
        logger.warning(f"[DATA] Neplatný název tabulky: '{tName}' z {request.remote_addr}")
        return jsonify({"error": "Neplatný název zařízení"}), 400

    values = (d.get('co2'), d.get('temp'), d.get('hum'), current_time)

    try:
        with sqlite3.connect('/root/home.db') as con:
            cur = con.cursor()
            cur.execute(f"CREATE TABLE IF NOT EXISTS {tName} (CO2 FLOAT, Temp FLOAT, Hum FLOAT, Tim TEXT)")
            cur.execute(f"INSERT INTO {tName} (CO2, Temp, Hum, Tim) VALUES (?, ?, ?, ?)", values)
            con.commit()
        logger.info(f"[DATA] Přijata data z '{tName}': CO2={values[0]}, Temp={values[1]}, Hum={values[2]}")
        return "OK"
    except Exception as e:
        logger.error(f"[DATA] Chyba při zápisu do DB pro '{tName}': {e}")
        return "ERROR", 500


@app.route('/api/widget/add', methods=['POST'])
def add_widget():
    data = request.get_json()
    new_id = f'widget-{next(widget_id_counter)}'
    widget = {
        'id': new_id,
        'title': data.get('title'),
        'table': data.get('type'),
        'sensor': data.get('sensor'),
        'calc': data.get('calc')
    }
    widgets.append(widget)
    logger.info(f"[WIDGET] Přidán widget '{widget['title']}' (id={new_id}, tabulka={widget['table']}, senzor={widget['sensor']})")
    return jsonify({'success': True, 'id': new_id})

@app.route('/api/widget/delete', methods=['POST'])
def delete_widget():
    global widgets
    widget_id_to_delete = request.get_json().get('id')
    initial_count = len(widgets)
    widgets = [w for w in widgets if w.get('id') != widget_id_to_delete]
    if len(widgets) < initial_count:
        logger.info(f"[WIDGET] Odstraněn widget id={widget_id_to_delete}")
        return jsonify({'success': True})
    logger.warning(f"[WIDGET] Widget id={widget_id_to_delete} nenalezen při mazání")
    return jsonify({'success': False, 'message': 'Widget not found'}), 404

@app.route('/api/widget/data/<widget_id>')
def widget_data(widget_id):
    widget = next((w for w in widgets if w['id'] == widget_id), None)
    if not widget:
        logger.warning(f"[WIDGET] Data požadována pro neexistující widget id={widget_id}")
        return jsonify({'error': 'Not found'}), 404
    data = get_widget_data(widget['table'], widget['sensor'], widget['calc'])
    return jsonify(data)

@app.route('/api/widget/history/<widget_id>')
def widget_history(widget_id):
    widget = next((w for w in widgets if w['id'] == widget_id), None)
    if not widget:
        logger.warning(f"[WIDGET] Historie požadována pro neexistující widget id={widget_id}")
        return jsonify({'error': 'Not found'}), 404
    data = get_historical_data(
        table_name=widget['table'],
        column_name=widget['sensor'],
        range_type=request.args.get('range'),
        start_date=request.args.get('start'),
        end_date=request.args.get('end')
    )
    return jsonify(data)


@app.route('/api/relay/<int:relay_id>/<string:action>', methods=['POST'])
def control_relay(relay_id, action):
    try:
        publish.single(f"relay/relay{relay_id}", action.lower(), hostname="10.42.0.1")
        logger.info(f"[RELAY] Relé {relay_id} → {action.upper()}")
        return jsonify({"status": "sent", "relay": relay_id, "action": action})
    except Exception as e:
        logger.error(f"[RELAY] Chyba při odesílání MQTT pro relé {relay_id}: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route('/api/settings', methods=['GET'])
def get_settings():
    return jsonify(get_config())

@app.route('/api/settings', methods=['POST'])
def save_settings():
    try:
        new_config = request.get_json()
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(new_config, f)
        logger.info(f"[SETTINGS] Nastavení uložena: {new_config}")
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"[SETTINGS] Chyba při ukládání nastavení: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/automation/add', methods=['POST'])
def add_automation():
    d = request.get_json()
    d['id'] = str(uuid.uuid4())
    d['relay_state'] = 'OFF'
    automations.append(d)
    logger.info(f"[AUTO] Přidána automatizace '{d['title']}' (relé={d['relay']}, ON>{d['threshold_on']}, OFF<{d['threshold_off']})")
    return jsonify({'success': True, 'id': d['id']})

@app.route('/api/automation/list', methods=['GET'])
def list_automations():
    return jsonify(automations)

@app.route('/api/automation/delete', methods=['POST'])
def delete_automation():
    global automations
    aid = request.get_json().get('id')
    before = len(automations)
    automations = [a for a in automations if a['id'] != aid]
    if len(automations) < before:
        logger.info(f"[AUTO] Odstraněna automatizace id={aid}")
    else:
        logger.warning(f"[AUTO] Automatizace id={aid} nenalezena při mazání")
    return jsonify({'success': True})


@app.before_request
def before_request():
    ip = request.remote_addr

    if is_rate_limited(ip):
        logger.warning(f"[RATE] Rate limit překročen pro {ip}")
        return jsonify({"error": "Too many requests"}), 429

    logger.info(f"[REQUEST] {request.method} {request.path} – from {ip}")

    if request.is_json and request.path != '/data':
        try:
            logger.debug(f"[REQUEST] body: {request.get_json()}")
        except Exception:
            pass


@app.after_request
def after_request(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'

    logger.info(f"[RESPONSE] {request.method} {request.path} → {response.status_code}")
    return response


@app.errorhandler(404)
def not_found(e):
    logger.warning(f"[404] Endpoint nenalezen: {request.method} {request.path}")
    return jsonify({"error": "Endpoint nenalezen"}), 404


@app.errorhandler(500)
def server_error(e):
    logger.error(f"[500] Interní chyba serveru: {request.method} {request.path} – {e}")
    return jsonify({"error": "Interní chyba serveru"}), 500

if __name__ == "__main__":
    worker_thread = threading.Thread(target=automation_worker, args=(automations,), daemon=True)
    worker_thread.start()
    logger.info("API server se spouští na portu 8070...")
    app.run(host="0.0.0.0", port=8070, debug=False)