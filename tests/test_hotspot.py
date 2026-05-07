import os
import sys
import importlib
import pytest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def hotspot():
    run = MagicMock(return_value=MagicMock(returncode=0))
    sub = MagicMock()
    sub.run = run
    sub.CalledProcessError = Exception
    sys.modules['subprocess'] = sub
    from src.tools import hotspot as h; importlib.reload(h)
    return h, run


# ── start_hotspot ──────────────────────────────────────────────

def test_start_calls_run(hotspot):
    h, run = hotspot
    h.start_hotspot('Net', 'pass')
    run.assert_called_once()

def test_start_passes_ssid(hotspot):
    h, run = hotspot
    h.start_hotspot('MySSID', 'pass')
    assert 'MySSID' in run.call_args[0][0]

def test_start_passes_password(hotspot):
    h, run = hotspot
    h.start_hotspot('Net', 'secret')
    assert 'secret' in run.call_args[0][0]

def test_start_uses_hotspot_subcommand(hotspot):
    h, run = hotspot
    h.start_hotspot('Net', 'pass')
    assert 'hotspot' in run.call_args[0][0]

def test_start_silent_on_error(hotspot):
    h, run = hotspot
    run.side_effect = Exception("nmcli failed")
    h.start_hotspot('Net', 'pass')  # should not raise


# ── stop_hotspot ───────────────────────────────────────────────

def test_stop_calls_run(hotspot):
    h, run = hotspot
    h.stop_hotspot()
    run.assert_called_once()

def test_stop_uses_down(hotspot):
    h, run = hotspot
    h.stop_hotspot()
    assert 'down' in run.call_args[0][0]

def test_stop_targets_hotspot(hotspot):
    h, run = hotspot
    h.stop_hotspot()
    assert 'Hotspot' in run.call_args[0][0]

def test_stop_silent_on_error(hotspot):
    h, run = hotspot
    run.side_effect = Exception("nmcli failed")
    h.stop_hotspot()  # should not raise