from flask import Flask, render_template, request, redirect, url_for, session
import random
import socket
import uuid

app = Flask(__name__)
app.secret_key = "smart_home_secret"

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
def index():
    data = get_sensor_data()
    dark_mode = session.get("dark_mode", False)
    return render_template("index.html", data=data, dark_mode=dark_mode)

@app.route('/settings', methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        if "dark_mode" in request.form:
            session["dark_mode"] = (request.form["dark_mode"] == "on")
        return redirect(url_for('settings'))

    dark_mode = session.get("dark_mode", False)
    network_info = get_network_info()
    return render_template("settings.html", dark_mode=dark_mode, network=network_info)

@app.route('/test')
def test():
    return "<h1>Hello Smart Home</h1>"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)

