import os
import sys
import importlib
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.modules.setdefault('paho', MagicMock())
sys.modules.setdefault('paho.mqtt', MagicMock())
sys.modules.setdefault('paho.mqtt.publish', MagicMock())


def _rule(state='OFF', on=30.0, off=25.0):
    return {
        'id': '1', 'title': 'Test', 'table': 'room',
        'sensor': 'Temp', 'calc': 'last', 'relay': 1,
        'threshold_on': on, 'threshold_off': off, 'relay_state': state,
    }


@pytest.fixture
def worker():
    """Returns a callable: run(rules, value) → publish.single mock."""
    def _run(rules, value):
        from src.tools import automation as m; importlib.reload(m)
        pub = MagicMock()
        m.publish = MagicMock(); m.publish.single = pub
        with patch.object(m, 'get_widget_data', return_value={'value': value, 'timestamp': 'x'}):
            with patch('time.sleep', side_effect=[None, StopIteration]):
                try: m.automation_worker(rules)
                except StopIteration: pass
        return pub
    return _run


# ── relay ON ──────────────────────────────────────────────────

def test_turns_on_above_threshold(worker):
    rules = [_rule()]
    worker(rules, 32.0)
    assert rules[0]['relay_state'] == 'ON'

def test_sends_on_mqtt(worker):
    pub = worker([_rule()], 32.0)
    pub.assert_called_with('relay/relay1', 'on', hostname='10.42.0.1')


# ── relay OFF ─────────────────────────────────────────────────

def test_turns_off_below_threshold(worker):
    rules = [_rule(state='ON')]
    worker(rules, 20.0)
    assert rules[0]['relay_state'] == 'OFF'

def test_sends_off_mqtt(worker):
    pub = worker([_rule(state='ON')], 20.0)
    pub.assert_called_with('relay/relay1', 'off', hostname='10.42.0.1')


# ── idempotency ───────────────────────────────────────────────

def test_no_toggle_already_on(worker):
    worker([_rule(state='ON')], 35.0).assert_not_called()

def test_no_toggle_already_off(worker):
    worker([_rule(state='OFF')], 10.0).assert_not_called()

def test_no_action_in_hysteresis_band(worker):
    worker([_rule(state='OFF')], 27.5).assert_not_called()


# ── edge cases ────────────────────────────────────────────────

def test_dash_value_skipped(worker):
    worker([_rule()], '--').assert_not_called()

def test_exception_does_not_crash_worker():
    from src.tools import automation as m; importlib.reload(m)
    m.publish = MagicMock()
    with patch.object(m, 'get_widget_data', side_effect=Exception("db gone")):
        with patch('time.sleep', side_effect=[None, StopIteration]):
            try: m.automation_worker([_rule()])
            except StopIteration: pass
            except Exception as e: pytest.fail(f"Worker crashed: {e}")