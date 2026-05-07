import itertools
from flask import Flask, render_template, request, redirect, url_for, jsonify
import socket
import uuid
import os
import json
from src.tools.hotspot import start_hotspot, stop_hotspot
from src.tools.dbTools import get_db_tables

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = "smart_home_secret"
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

@app.route('/')
def home():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    db_tables = get_db_tables()
    return render_template('dashboard.html', widgets=widgets, db_tables=db_tables)

@app.route('/automation')
def automation():
    db_tables = get_db_tables()
    return render_template('automation.html', db_tables=db_tables)

@app.route('/settings')
def settings():
    config = get_config()
    return render_template('settings.html', config=config)

if __name__ == '__main__':
    start_hotspot(ssid="test", password="test1234")
    app.run(host='0.0.0.0', port=8000, debug=True)
