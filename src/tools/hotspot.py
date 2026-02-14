import subprocess

def start_hotspot(ssid, password):
    try:
        subprocess.run([
            "sudo", "nmcli", "device", "wifi", "hotspot",
            "ssid", ssid,
            "password", password
        ], check=True)
        print("Hotspot started!")
    except subprocess.CalledProcessError as e:
        print("Error starting hotspot:", e)

def stop_hotspot():
    try:
        subprocess.run([
            "nmcli", "connection", "down", "Hotspot"
        ], check=True)

        print("Hotspot stopped!")

    except subprocess.CalledProcessError as e:
        print("Error stopping hotspot:", e)