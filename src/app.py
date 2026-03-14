import itertools
from tools.dbTools import get_db_tables
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import random
import socket
import uuid
from src.tools.hotspot import start_hotspot, stop_hotspot

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = "smart_home_secret"

widgets = []
widget_id_counter = itertools.count(1)


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
    title = data.get('title')
    widget_type = data.get('type')

    new_id = f'widget-{next(widget_id_counter)}'
    new_widget = {'id': new_id,'title': title,'type': widget_type}
    widgets.append(new_widget)

    return jsonify({'success': True,'id': new_id,'title': title,'type': widget_type})

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
    return render_template('settings.html')

if __name__ == '__main__':
    #stop_hotspot()
    start_hotspot(ssid="test", password="test1234")
    app.run(host='0.0.0.0', port=8000, debug=True)

