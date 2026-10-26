"""Быстрые тесты: PYTHONPATH=. python -m pytest tests/ -q"""
from pathlib import Path
import json

from scene import SLOTS, build_scene, effect_settings


def test_slots_no_overlaps():
    assert len(SLOTS) == len(set(SLOTS)) == 24
    for a, (x1, y1) in enumerate(SLOTS):
        for x2, y2 in SLOTS[a + 1:]:
            assert abs(x1 - x2) >= 202 or abs(y1 - y2) >= 70


def test_new_card_only_fresh():
    rows = [
        {"id": 2, "name": "Второй ученик", "answer": "Урок был интересный"},
        {"id": 1, "name": "Первый ученик", "answer": "Я всё понял"},
    ]
    result = build_scene(rows, {2}, "Білім Дос")
    assert result.count('class="note fresh"') == 1
    assert result.count('class="note-anchor"') == 2
    assert 'Всего ответов:' not in result
    assert 'Учитель' not in result


def test_html_escaping():
    rows = [{"id": 1, "name": '<script>alert(1)</script>',
             "answer": '</script><svg onload=alert(1)>'}]
    markup = build_scene(rows, {1}, '<img src=x onerror=alert(1)>')
    assert '<script>alert(1)</script>' not in markup
    assert '<svg onload=alert(1)>' not in markup
    assert '&lt;img src=x' in markup
    assert '&lt;script&gt;' in markup


def test_effect_limits():
    cfg = effect_settings()
    assert 0 <= cfg['particle_count'] <= 32
    assert 2 <= cfg['refresh_seconds'] <= 15
    assert 450 <= cfg['arrival_duration_ms'] <= 2600


def test_json_file():
    path = Path(__file__).resolve().parent.parent / 'effects.json'
    assert isinstance(json.loads(path.read_text(encoding='utf-8')), dict)
