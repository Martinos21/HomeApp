from src.tools.dbTools import get_widget_data
import paho.mqtt.publish as publish
import time


def automation_worker(automations):
    while True:
        for a in automations:
            try:
                data = get_widget_data(a['table'], a['sensor'], a['calc'])
                value = data.get('value')
                if value is None or value == '--':
                    continue
                value = float(value)

                if value > a['threshold_on'] and a['relay_state'] != 'ON':
                    publish.single(f"relay/relay{a['relay']}", 'on', hostname='10.42.0.1')
                    a['relay_state'] = 'ON'
                    print(f"[AUTO] {a['title']}: hodnota {value} > {a['threshold_on']} → relé {a['relay']} ON")

                elif value < a['threshold_off'] and a['relay_state'] != 'OFF':
                    publish.single(f"relay/relay{a['relay']}", 'off', hostname='10.42.0.1')
                    a['relay_state'] = 'OFF'
                    print(f"[AUTO] {a['title']}: hodnota {value} < {a['threshold_off']} → relé {a['relay']} OFF")

            except Exception as e:
                print(f"[AUTO ERROR] {a['title']}: {e}")

        time.sleep(30)