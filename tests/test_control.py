import sqlite3
from datetime import datetime, timezone

import pytest
from control import initialize_controls, read_controls, save_controls, signal_event


def make_connection():
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute('CREATE TABLE settings(key TEXT PRIMARY KEY,value TEXT NOT NULL)')
    initialize_controls(conn)
    return conn


def test_teacher_controls_saved():
    with make_connection() as conn:
        save_controls(conn, {
            'fx_mascot': False, 'fx_particles': True,
            'fx_theme': 'lavender', 'fx_particle_count': 24,
            'fx_arrival_duration_ms': 1200,
        })
        config = read_controls(conn)
        assert config['fx_mascot'] is False
        assert config['fx_particles'] is True
        assert config['fx_theme'] == 'lavender'
        assert config['fx_particle_count'] == 24
        assert config['fx_arrival_duration_ms'] == 1200


def test_event_signals_are_persisted_and_stop():
    now = datetime(2026, 10, 26, 14, 0, tzinfo=timezone.utc)
    with make_connection() as conn:
        signal_event(conn, 'show', now=now)
        assert read_controls(conn)['show_started_at'] == '2026-10-26T14:00:00.000+00:00'
        signal_event(conn, 'stop')
        assert read_controls(conn)['show_started_at'] == ''
        signal_event(conn, 'demo', now=now)
        assert read_controls(conn)['demo_started_at'].startswith('2026-10-26')


def test_unknown_and_out_of_range_controls_are_rejected():
    with make_connection() as conn:
        with pytest.raises(ValueError):
            save_controls(conn, {'fx_particle_count': 1000})
        with pytest.raises(ValueError):
            save_controls(conn, {'debug_password': 'abc'})
        with pytest.raises(ValueError):
            save_controls(conn, {'fx_enabled': 'false'})
        with pytest.raises(ValueError):
            signal_event(conn, 'other')


def test_read_malformed_db_values_are_clamped():
    with make_connection() as conn:
        conn.execute("UPDATE settings SET value='123456' WHERE key='fx_particle_count'")
        conn.execute("UPDATE settings SET value='broken' WHERE key='fx_arrival_duration_ms'")
        conf = read_controls(conn)
        assert conf['fx_particle_count'] == 32
        assert conf['fx_arrival_duration_ms'] == 1450
