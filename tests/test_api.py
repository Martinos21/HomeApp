import os
import sys
import tempfile
import importlib
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.modules.setdefault('paho', MagicMock())
sys.modules.setdefault('paho.mqtt', MagicMock())
sys.modules.setdefault('paho.mqtt.publish', MagicMock())
_cors = MagicMock(); _cors.CORS = lambda app, **kw: app
sys.modules.setdefault('flask_cors', _cors)
_sub = MagicMock(); _sub.CalledProcessError = Exception
sys.modules['subprocess'] = _sub


@pytest.fixture
def client():
    from api import api; importlib.reload(api)
    api.app.config['TESTING'] = True
    api.widgets.clear(); api.automations.clear()
    return api.app.test_client(), api


@pytest.fixture
def widget(client):
    c, api = client
    r = c.post('/api/widget/add', json={
        'title': 'T', 'type': 'room', 'sensor': 'Temp', 'calc': 'last'})
    return r.get_json()['id']


# ── widgets ───────────────────────────────────────────────────

def test_add_widget(client):
    c, api = client
    r = c.post('/api/widget/add', json={'title':'T','type':'room','sensor':'Temp','calc':'last'})
    assert r.get_json()['success'] is True
    assert len(api.widgets) == 1

def test_delete_widget(client, widget):
    c, api = client
    c.post('/api/widget/delete', json={'id': widget})
    assert len(api.widgets) == 0

def test_delete_unknown_widget(client):
    c, _ = client
    assert c.post('/api/widget/delete', json={'id': 'x'}).status_code == 404

def test_widget_data_unknown(client):
    c, _ = client
    assert c.get('/api/widget/data/x').status_code == 404

def test_widget_data_returns_value(client, widget):
    c, api = client
    with patch.object(api, 'get_widget_data', return_value={'value': 21.5, 'timestamp': 'x'}):
        r = c.get(f'/api/widget/data/{widget}')
    assert r.get_json()['value'] == 21.5

def test_widget_history_unknown(client):
    c, _ = client
    assert c.get('/api/widget/history/x').status_code == 404

def test_widget_history_returns_data(client, widget):
    c, api = client
    hist = {'values': [20, 21], 'labels': ['a', 'b'], 'latest_timestamp': 'x'}
    with patch.object(api, 'get_historical_data', return_value=hist):
        r = c.get(f'/api/widget/history/{widget}?range=week')
    assert r.get_json()['values'] == [20, 21]


# ── relay ─────────────────────────────────────────────────────

def test_relay_on(client):
    c, _ = client
    assert c.post('/api/relay/1/ON').status_code == 200

def test_relay_response_shape(client):
    c, _ = client
    data = c.post('/api/relay/2/OFF').get_json()
    assert data['relay'] == 2
    assert data['action'] == 'OFF'

def test_relay_sends_mqtt(client):
    c, api = client
    with patch.object(api, 'publish') as mp:
        c.post('/api/relay/1/ON')
    mp.single.assert_called_once_with('relay/relay1', 'on', hostname='10.42.0.1')


# ── settings ──────────────────────────────────────────────────

def test_get_settings_default_keys(client):
    c, _ = client
    with patch('os.path.exists', return_value=False):
        data = c.get('/api/settings').get_json()
    for k in ('username', 'email', 'refresh', 'temp_unit', 'security'):
        assert k in data

def test_save_settings(client):
    c, api = client
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        tmp = f.name
    try:
        with patch.object(api, 'SETTINGS_FILE', tmp):
            r = c.post('/api/settings', json={
                'username': 'X', 'email': '', 'refresh': '30', 'temp_unit': 'c', 'security': False})
        assert r.get_json()['success'] is True
    finally:
        os.unlink(tmp)


# ── automation ────────────────────────────────────────────────

PAYLOAD = {'title':'Fan','table':'room','sensor':'Temp',
           'calc':'last','relay':1,'threshold_on':28.0,'threshold_off':24.0}

def test_add_automation(client):
    c, api = client
    r = c.post('/api/automation/add', json=PAYLOAD)
    assert r.get_json()['success'] is True
    assert api.automations[0]['relay_state'] == 'OFF'

def test_list_automations(client):
    c, _ = client
    c.post('/api/automation/add', json=PAYLOAD)
    assert len(c.get('/api/automation/list').get_json()) == 1

def test_delete_automation(client):
    c, api = client
    aid = c.post('/api/automation/add', json=PAYLOAD).get_json()['id']
    c.post('/api/automation/delete', json={'id': aid})
    assert len(api.automations) == 0


# ── error handlers ────────────────────────────────────────────

def test_404_on_unknown_endpoint(client):
    c, _ = client
    assert c.get('/api/nope').status_code == 404