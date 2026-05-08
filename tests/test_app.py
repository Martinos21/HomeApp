import os
import sys
import json
import sqlite3
import tempfile
import importlib
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def client():
    sub = MagicMock()
    sub.run = MagicMock(return_value=MagicMock(returncode=0))
    sub.CalledProcessError = Exception
    sys.modules['subprocess'] = sub
    with patch('sqlite3.connect', return_value=sqlite3.connect(':memory:')):
        from src import app; importlib.reload(app)
    app.app.config['TESTING'] = True
    return app.app.test_client(), app


# ── routes ────────────────────────────────────────────────────

def test_root_redirects_to_dashboard(client):
    c, _ = client
    r = c.get('/')
    assert r.status_code == 302
    assert '/dashboard' in r.headers['Location']

def test_dashboard_returns_200(client):
    c, app = client
    with patch.object(app, 'get_db_tables', return_value=['room']):
        assert c.get('/dashboard').status_code == 200

def test_settings_returns_200(client):
    c, _ = client
    with patch('os.path.exists', return_value=False):
        assert c.get('/settings').status_code == 200

def test_automation_returns_200(client):
    c, app = client
    with patch.object(app, 'get_db_tables', return_value=['room']):
        assert c.get('/automation').status_code == 200

def test_settings_renders_username(client):
    c, app = client
    cfg = {'username': 'TestUser', 'email': '', 'refresh': '30', 'temp_unit': 'c', 'security': False}
    with patch.object(app, 'get_config', return_value=cfg):
        assert b'TestUser' in c.get('/settings').data


# ── get_config ────────────────────────────────────────────────

def test_config_defaults(client):
    _, app = client
    with patch('os.path.exists', return_value=False):
        cfg = app.get_config()
    assert cfg['temp_unit'] == 'c'
    assert 'username' in cfg

def test_config_loads_from_file(client):
    _, app = client
    data = {'username': 'FileUser', 'email': '', 'refresh': '30', 'temp_unit': 'f', 'security': False}
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f); tmp = f.name
    try:
        with patch.object(app, 'SETTINGS_FILE', tmp):
            assert app.get_config()['username'] == 'FileUser'
    finally:
        os.unlink(tmp)

def test_config_falls_back_on_corrupt_file(client):
    _, app = client
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{{INVALID}}"); tmp = f.name
    try:
        with patch.object(app, 'SETTINGS_FILE', tmp):
            assert 'username' in app.get_config()
    finally:
        os.unlink(tmp)