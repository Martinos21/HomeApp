import os
import sys
import sqlite3
import pytest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.tools import dbTools

DB = '/tmp/test_dbtools.db'


@pytest.fixture(autouse=True)
def fresh_db():
    con = sqlite3.connect(DB)
    con.execute("DROP TABLE IF EXISTS room")
    con.execute("CREATE TABLE room (CO2 FLOAT, Temp FLOAT, Hum FLOAT, Tim TEXT)")
    con.executemany("INSERT INTO room VALUES (?,?,?,?)", [
        (400, 20.0, 50.0, '2026-01-01 10:00:00'),
        (500, 22.5, 55.0, '2026-01-02 10:00:00'),
        (600, 25.0, 60.0, '2026-01-03 10:00:00'),
    ])
    con.commit(); con.close()
    yield
    if os.path.exists(DB):
        os.remove(DB)


@pytest.fixture
def db():
    return patch('src.tools.dbTools.sqlite3.connect', return_value=sqlite3.connect(DB))


# ── get_db_tables ──────────────────────────────────────────────

def test_get_db_tables_returns_list(db):
    with db: assert isinstance(dbTools.get_db_tables(), list)

def test_get_db_tables_contains_table(db):
    with db: assert 'room' in dbTools.get_db_tables()

def test_get_db_tables_no_internal_tables(db):
    with db:
        for t in dbTools.get_db_tables():
            assert not t.startswith('sqlite_')


# ── get_widget_data ────────────────────────────────────────────

def test_widget_data_last(db):
    with db: assert dbTools.get_widget_data('room', 'Temp', 'last')['value'] == 25.0

def test_widget_data_min(db):
    with db: assert dbTools.get_widget_data('room', 'Temp', 'min')['value'] == 20.0

def test_widget_data_max(db):
    with db: assert dbTools.get_widget_data('room', 'Temp', 'max')['value'] == 25.0

def test_widget_data_avg(db):
    with db: assert abs(dbTools.get_widget_data('room', 'Temp', 'avg')['value'] - 22.5) < 0.1

def test_widget_data_timestamp(db):
    with db: assert '2026-01-03' in dbTools.get_widget_data('room', 'Temp', 'last')['timestamp']

def test_widget_data_bad_table(db):
    with db: assert dbTools.get_widget_data('nope', 'Temp', 'last')['value'] in ['Err', '--']


# ── get_historical_data ────────────────────────────────────────

def test_historical_all_rows(db):
    with db: assert len(dbTools.get_historical_data('room', 'Temp')['values']) == 3

def test_historical_ascending(db):
    with db: assert dbTools.get_historical_data('room', 'Temp')['values'] == [20.0, 22.5, 25.0]

def test_historical_start_date(db):
    with db:
        r = dbTools.get_historical_data('room', 'Temp', start_date='2026-01-02 00:00:00')
    assert len(r['values']) == 2

def test_historical_start_and_end(db):
    with db:
        r = dbTools.get_historical_data('room', 'Temp',
            start_date='2026-01-02 00:00:00', end_date='2026-01-02 23:59:59')
    assert r['values'] == [22.5]

def test_historical_week_range_old_data(db):
    with db:
        r = dbTools.get_historical_data('room', 'Temp', range_type='week')
    assert r['values'] == []

def test_historical_empty_table(db):
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE empty (CO2 FLOAT, Temp FLOAT, Hum FLOAT, Tim TEXT)")
    con.commit(); con.close()
    with db:
        r = dbTools.get_historical_data('empty', 'Temp')
    assert r['values'] == []
    assert r['latest_timestamp'] is None