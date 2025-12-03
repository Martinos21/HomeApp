import subprocess

SSID = "MyHotspot"
PASSWORD = "12345678"  # Must be 8+ chars
BAND = "wifi"  # or "wifi2" for 5 GHz, depending on system

def start_hotspot(ssid, password):
    try:
        subprocess.run([
            "nmcli", "device", "wifi", "hotspot",
            "ssid", ssid,
            "password", password
        ], check=True)
        print("Hotspot started!")
    except subprocess.CalledProcessError as e:
        print("Error starting hotspot:", e)

start_hotspot(SSID, PASSWORD)



