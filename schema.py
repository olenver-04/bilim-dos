"""Database setup and backward-compatible imports from Bilim Dos V3/V4."""
from __future__ import annotations

from control import initialize_controls

CREATE_RESPONSES = (
    'CREATE TABLE IF NOT EXISTS responses ('
    'id INTEGER PRIMARY KEY AUTOINCREMENT, '
    'name TEXT NOT NULL, answer TEXT NOT NULL, created TEXT NOT NULL)'
)


def initialize_schema(conn, lesson_defaults):
    conn.execute(CREATE_RESPONSES)
    cols = {r['name'] for r in conn.execute('PRAGMA table_info(responses)')}
    expected = {'id', 'name', 'answer', 'created'}
    legacy = {'id', 'student_name', 'message', 'created_at'}
    if not expected.issubset(cols) and legacy.issubset(cols):
        # The V3 schema (and the original Kazakh template) used these names.
        # Rename in a transaction before recreating, so rows are not lost.
        conn.execute('ALTER TABLE responses RENAME TO responses_before_v5')
        conn.execute(CREATE_RESPONSES)
        conn.execute('INSERT INTO responses(id,name,answer,created) '
                     'SELECT id,student_name,message,created_at FROM responses_before_v5')
        conn.execute('DROP TABLE responses_before_v5')
    elif not expected.issubset(cols):
        raise RuntimeError('Неизвестная структура таблицы ответов: не перезаписываю данные.')

    conn.execute('CREATE TABLE IF NOT EXISTS settings ('
                 'key TEXT PRIMARY KEY, value TEXT NOT NULL)')
    existing = {r['key']: r['value'] for r in conn.execute('SELECT key,value FROM settings')}
    old_names = {'school': 'school_name', 'topic': 'lesson_title',
                 'question': 'reflection_question'}
    for new, old in old_names.items():
        if new not in existing and old in existing:
            conn.execute('INSERT INTO settings(key,value) VALUES (?,?)',
                         (new, existing[old]))
    conn.executemany('INSERT OR IGNORE INTO settings(key,value) VALUES (?,?)',
                     lesson_defaults.items())
    initialize_controls(conn)
