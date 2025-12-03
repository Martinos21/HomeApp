from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import random
import socket
import uuid

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = "smart_home_secret"

widgets = []

# Simulate sensor data
def get_sensor_data():
    return {
        "temperature": round(random.uniform(20, 25), 2),
        "humidity": round(random.uniform(40, 60), 2),
        "co2": random.randint(400, 800)
    }

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
    return render_template('dashboard.html', widgets=widgets)

@app.route('/add_widget', methods=['POST'])
def add_widget():
    data = request.get_json()
    title = data.get('title')
    widget_type = data.get('type')

    # You can store this in DB later
    return jsonify({
        'success': True,
        'title': title,
        'type': widget_type
    })

@app.route('/devices')
def devices():
    return render_template('devices.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)

