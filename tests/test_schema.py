import sqlite3
from schema import initialize_schema


def test_legacy_data_and_settings_preserved():
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.executescript('''
        CREATE TABLE responses(id INTEGER PRIMARY KEY, student_name TEXT NOT NULL,
            activity TEXT, message TEXT NOT NULL, created_at TEXT NOT NULL);
        INSERT INTO responses VALUES (7,'Алия','reflection','Мне понравилось','2026-10-26T00:00:00Z');
        CREATE TABLE settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        INSERT INTO settings VALUES ('school_name','Школа № 1');
        INSERT INTO settings VALUES ('lesson_title','Математика');
    ''')
    defaults = {'school':'Білім Дос','topic':'Рефлексия урока','question':'Что узнал?'}
    initialize_schema(conn, defaults)
    assert conn.execute('SELECT name,answer FROM responses WHERE id=7').fetchone()['name'] == 'Алия'
    assert conn.execute("SELECT value FROM settings WHERE key='school'").fetchone()[0] == 'Школа № 1'
    initialize_schema(conn, defaults)
    assert conn.execute('SELECT COUNT(*) FROM responses').fetchone()[0] == 1
    conn.close()
