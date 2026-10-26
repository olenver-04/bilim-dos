"""Persistent teacher show controls, shared by projector sessions via SQLite.

This module has no Streamlit dependency; values are validated before storage.
"""
from __future__ import annotations

from datetime import datetime, timezone

BOOL_KEYS = (
    'fx_enabled', 'fx_mascot', 'fx_ambient', 'fx_arrival',
    'fx_particles', 'fx_toast', 'fx_finale',
)
INT_LIMITS = {
    'fx_particle_count': (0, 32),
    'fx_arrival_duration_ms': (500, 2400),
}
CHOICES = {'fx_theme': ('sky', 'lavender', 'mint')}
DEFAULTS = {
    'fx_enabled': '1',
    'fx_mascot': '1',
    'fx_ambient': '1',
    'fx_arrival': '1',
    'fx_particles': '1',
    'fx_toast': '1',
    'fx_finale': '1',
    'fx_particle_count': '18',
    'fx_arrival_duration_ms': '1450',
    'fx_theme': 'sky',
    'show_started_at': '',
    'demo_started_at': '',
}


def initialize_controls(conn):
    """Run after creating the settings(key, value) table."""
    conn.executemany(
        'INSERT OR IGNORE INTO settings(key,value) VALUES (?,?)',
        DEFAULTS.items(),
    )


def read_controls(conn):
    rows = dict(DEFAULTS)
    rows.update({r['key']: r['value'] for r in conn.execute(
        'SELECT key,value FROM settings WHERE key IN ('
        + ','.join('?' for _ in DEFAULTS) + ')', tuple(DEFAULTS)
    )})
    config = {}
    for key in BOOL_KEYS:
        config[key] = rows[key] == '1'
    for key, (low, high) in INT_LIMITS.items():
        try:
            n = int(rows[key])
        except (ValueError, TypeError):
            n = int(DEFAULTS[key])
        config[key] = max(low, min(high, n))
    for key, options in CHOICES.items():
        config[key] = rows[key] if rows[key] in options else DEFAULTS[key]
    config['show_started_at'] = rows['show_started_at']
    config['demo_started_at'] = rows['demo_started_at']
    return config


def save_controls(conn, data):
    entries = []
    for key, value in data.items():
        if key in BOOL_KEYS:
            if not isinstance(value, bool):
                raise ValueError('Ожидается включено/выключено: ' + key)
            raw = '1' if value else '0'
        elif key in INT_LIMITS:
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError('Неверное число: ' + key)
            lo, hi = INT_LIMITS[key]
            if value < lo or value > hi:
                raise ValueError('Значение вне диапазона: ' + key)
            raw = str(value)
        elif key in CHOICES:
            if value not in CHOICES[key]:
                raise ValueError('Неизвестное оформление')
            raw = value
        else:
            raise ValueError('Неизвестная настройка: ' + key)
        entries.append((key, raw))
    conn.executemany(
        'INSERT INTO settings(key,value) VALUES (?,?) '
        'ON CONFLICT(key) DO UPDATE SET value=excluded.value',
        entries,
    )


def signal_event(conn, kind, now=None):
    """A timestamp makes the event visible to every wall client on its next refresh."""
    if kind not in ('show', 'demo', 'stop'):
        raise ValueError('Unknown stage event')
    key = 'demo_started_at' if kind == 'demo' else 'show_started_at'
    value = '' if kind == 'stop' else (now or datetime.now(timezone.utc)).isoformat(
        timespec='milliseconds'
    )
    conn.execute(
        'INSERT INTO settings(key,value) VALUES (?,?) '
        'ON CONFLICT(key) DO UPDATE SET value=excluded.value',
        (key, value),
    )
    return value
