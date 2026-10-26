"""Визуальная сцена Білім Дос: безопасный SVG + CSS + JSON + JS.

Весь пользовательский текст HTML-экранируется. При обновлении фрагмента
Streamlit эффекты запускаются только для новых id, пришедших из app.py.
"""
from __future__ import annotations

import html
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Iterable

ROOT = Path(__file__).parent
# Чередуем стороны: первые четыре ответа распределяются вокруг талисмана,
# а при полном классе все 24 непересекающиеся позиции будут заняты.
SLOTS = (
    (715, 90), (1290, 444), (715, 820), (140, 444),
    (495, 90), (1290, 268), (935, 820), (140, 620),
    (935, 90), (1290, 620), (495, 820), (140, 268),
    (275, 90), (1290, 180), (1155, 820), (140, 708),
    (1155, 90), (1290, 708), (275, 820), (140, 180),
    (140, 356), (1290, 356), (140, 532), (1290, 532),
)

PALETTE = (
    ("#3564D8", "#EFF4FF"),
    ("#E18A46", "#FFF3E9"),
    ("#0F9A85", "#E7F9F5"),
    ("#BD6EAD", "#FFF1FA"),
    ("#8870D0", "#F2F0FF"),
    ("#D37164", "#FFF1ED"),
)
EFFECT_DEFAULTS = {
    "enabled": True,
    "ambient_animation": True,
    "arrival_animation": True,
    "particles_enabled": True,
    "toast_enabled": True,
    "particle_count": 18,
    "max_celebrations_per_refresh": 3,
    "arrival_duration_ms": 1450,
    "toast_duration_ms": 3600,
    "refresh_seconds": 3,
}


def effect_settings():
    """Мягкая валидация JSON-конфигурации без eval или сетевых запросов."""
    raw = {}
    file = ROOT / 'effects.json'
    try:
        raw = json.loads(file.read_text(encoding='utf-8'))
        if not isinstance(raw, dict):
            raw = {}
    except (OSError, json.JSONDecodeError):
        pass
    result = dict(EFFECT_DEFAULTS)
    for key, default in EFFECT_DEFAULTS.items():
        value = raw.get(key, default)
        if isinstance(default, bool):
            result[key] = value if isinstance(value, bool) else default
        elif isinstance(value, int) and not isinstance(value, bool):
            limits = {
                'particle_count': (0, 32),
                'max_celebrations_per_refresh': (0, 4),
                'arrival_duration_ms': (450, 2600),
                'toast_duration_ms': (1400, 8000),
                'refresh_seconds': (2, 15),
                'finale_duration_ms': (12000, 30000),
            }
            lo, hi = limits[key]
            result[key] = max(lo, min(hi, value))
    return result


def esc(value):
    return html.escape(str(value), quote=True)


def short(value, maximum):
    return value if len(value) <= maximum else value[:maximum - 1].rstrip() + '…'


def stars():
    rng = random.Random(45)
    output = []
    for i in range(24):
        x = rng.randint(48, 1392)
        y = rng.randint(54, 850)
        size = rng.choice([4, 5, 7, 9])
        color = ('#FFB955', '#9AB8F4', '#F6A9C4', '#72CDBB')[i % 4]
        output.append(
            f'<g class="ambient-star" transform="translate({x} {y})" '
            f'style="--twinkle-delay:{(i % 9) * -.63:.2f}s;'
            f'--twinkle-time:{3.3 + (i % 6) * .47:.2f}s" aria-hidden="true">'
            f'<path d="M0 {-size} Q1 -1 {size} 0 Q1 1 0 {size} Q-1 1 {-size} 0 Q-1 -1 0 {-size}Z" '
            f'fill="{color}" opacity=".72"/></g>'
        )
    return ''.join(output)


def character(school):
    """Нарисованный в SVG школьный талисман: учебник и ученик в академической шапочке."""
    return f'''<g class="halo" aria-hidden="true">
        <circle cx="720" cy="455" r="243" fill="#B5C8FF" opacity=".14"/>
        <circle cx="720" cy="455" r="229" fill="none" stroke="#A2B8EE" stroke-width="4" opacity=".48"/>
      </g>
      <ellipse cx="720" cy="624" rx="218" ry="29" fill="#BACAF0" opacity=".32"/>
      <g class="mascot" aria-hidden="true">
        <path d="M510 490 Q620 453 720 515 Q820 453 930 490 L930 626 Q820 594 720 649 Q620 594 510 626Z"
           fill="white" stroke="#355BC4" stroke-width="9"/>
        <path d="M720 515V648" stroke="#355BC4" stroke-width="7"/>
        <path d="M536 517Q630 496 690 540 M536 544Q630 523 690 565
                 M750 540Q820 495 904 517 M750 565Q830 524 904 543"
              fill="none" stroke="#DCE6FF" stroke-width="7" stroke-linecap="round"/>
        <path class="book-highlight" d="M548 590 Q622 569 687 602 M749 602 Q822 574 889 590"
              stroke="#A0BAF8" stroke-width="3.5" fill="none" stroke-linecap="round"/>
        <path d="M720 515V428" stroke="#FFB44D" stroke-width="15" stroke-linecap="round"/>
        <circle cx="720" cy="355" r="87" fill="#FFD577" stroke="#DC9846" stroke-width="7"/>
        <path d="M650 305Q720 264 790 305" fill="none" stroke="#A05E35" stroke-width="11" stroke-linecap="round"/>
        <circle class="eye" cx="689" cy="353" r="7" fill="#4B3E45"/>
        <circle class="eye" cx="752" cy="353" r="7" fill="#4B3E45"/>
        <path d="M690 383Q721 410 752 383" fill="none" stroke="#A75E58" stroke-width="7" stroke-linecap="round"/>
        <circle cx="666" cy="374" r="13" fill="#FBA89B" opacity=".75"/>
        <circle cx="772" cy="374" r="13" fill="#FBA89B" opacity=".75"/>
        <path d="M642 288L720 241 798 288 720 321Z" fill="#3158C8" stroke="#24499F" stroke-width="5"/>
        <g class="tassel">
          <path d="M780 289V333" stroke="#24499F" stroke-width="6"/>
          <circle cx="780" cy="337" r="9" fill="#FFB44D"/>
        </g>
        <path d="M647 290V270Q719 238 793 270V293" fill="none" stroke="#3158C8" stroke-width="17"/>
        <g class="arm-left">
          <path d="M610 460Q563 424 541 453" fill="none"
              stroke="#3158C8" stroke-width="12" stroke-linecap="round"/>
          <circle cx="541" cy="453" r="12" fill="#FFD577"/>
        </g>
        <g class="arm-right">
          <path d="M828 460Q871 424 898 453" fill="none"
              stroke="#3158C8" stroke-width="12" stroke-linecap="round"/>
          <circle cx="898" cy="453" r="12" fill="#FFD577"/>
        </g>
      </g>
      <g class="mascot-speech" aria-hidden="true">
        <rect x="838" y="184" rx="20" width="250" height="57"
              fill="#FFFFFF" stroke="#D6E2FC" stroke-width="3"/>
        <path d="M861 241L851 262L890 241" fill="#FFFFFF" stroke="#D6E2FC"
              stroke-width="3" stroke-linejoin="round"/>
        <path d="M865 242H889" stroke="white" stroke-width="5"/>
        <text id="mascot-text" x="963" y="221" text-anchor="middle"
              font-size="22" font-weight="900" fill="#3158C8">У тебя получится!</text>
      </g>
      <g class="school-plaque">
        <rect x="555" y="657" width="330" height="72" rx="30" fill="#3158C8" stroke="white" stroke-width="5"/>
        <text x="720" y="704" text-anchor="middle" font-size="30" font-weight="900" fill="white">{esc(short(school, 25))}</text>
        <text x="720" y="766" text-anchor="middle" font-size="23" font-weight="800" fill="#405F9F">Наши мысли после урока</text>
      </g>'''


def build_scene(rows: Iterable[Mapping], fresh_ids: set[int], school: str, effects=None, controls=None, lesson="Рефлексия урока"):
    """Вернуть готовую HTML-сцену; подходит и для предварительного просмотра в браузере."""
    effects = effects if effects is not None else effect_settings()
    connection, cards = [], []
    for item, (x, y) in zip(reversed(list(rows)), SLOTS):
        ident = int(item['id'])
        name = ' '.join(str(item['name']).split())
        answer = ' '.join(str(item['answer']).split())
        accent, paper = PALETTE[(ident - 1) % len(PALETTE)]
        new = ' fresh' if ident in fresh_ids else ''
        conn_id = f'data-id="{ident}"'
        connection.append(
            f'<path class="connection{new}" {conn_id} '
            f'd="M720 455 Q{(720+x)/2:.1f} {(455+y)/2-32:.1f} {x} {y}" '
            f'fill="none" stroke="{accent}" stroke-width="3.5"/>'
        )
        tooltip = esc(f'{name} — {answer}')
        cards.append(
            f'<g class="note-anchor" transform="translate({x} {y})">'
            f'<g class="note{new}" tabindex="0" '
            f'data-id="{ident}" data-student="{esc(name)}" '
            f'data-accent="{accent}" data-x="{x}" data-y="{y}" '
            f'style="--fly-x:{720-x}px;--fly-y:{455-y}px">'
            f'<title>{tooltip}</title>'
            f'<rect class="card-rect" x="-101" y="-35" width="202" height="70" rx="18" '
            f'fill="{paper}" stroke="{accent}" stroke-width="2.8"/>'
            f'<circle cx="-81" cy="-19" r="5.4" fill="{accent}" opacity=".75"/>'
            f'<text class="note-answer" x="0" y="-3" text-anchor="middle">'
            f'{esc(short(answer, 17))}</text>'
            f'<text class="note-name" x="0" y="20" text-anchor="middle" fill="{accent}">'
            f'{esc(short(name, 22))}</text>'
            '</g></g>'
        )

    payload = {
        'effects': effects,
        'controls': controls or {},
        'server_now': datetime.now(timezone.utc).isoformat(timespec='milliseconds'),
    }
    # Разрываем любые потенциальные HTML-теги, попавшие внутрь JSON.
    payload_json = (json.dumps(payload, ensure_ascii=False)
                    .replace('<', '\\u003c').replace('>', '\\u003e')
                    .replace('&', '\\u0026'))
    css = (ROOT / 'scene.css').read_text(encoding='utf-8')
    js = (ROOT / 'scene.js').read_text(encoding='utf-8')
    return f'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<style>{css}</style></head><body>
<div class="scene" id="reflection-scene">
  <svg class="cluster-svg" xmlns="http://www.w3.org/2000/svg"
       viewBox="0 0 1440 900" role="img"
       aria-label="Рефлексия школьного урока: мысли учеников" preserveAspectRatio="xMidYMid meet">
    <defs>
      <radialGradient id="bg"><stop stop-color="#FFF"/><stop offset="1" stop-color="#EAF2FF"/></radialGradient>
      <radialGradient id="bg-lavender"><stop stop-color="#FFF"/><stop offset="1" stop-color="#EEE5FF"/></radialGradient>
      <radialGradient id="bg-mint"><stop stop-color="#FFF"/><stop offset="1" stop-color="#DEF8EE"/></radialGradient>
      <pattern id="dots" width="44" height="44" patternUnits="userSpaceOnUse">
        <circle cx="4" cy="4" r="1.8" fill="#A9BDEB" opacity=".4"/>
      </pattern>
      <radialGradient id="golden"><stop stop-color="#FFE59B" stop-opacity=".45"/>
        <stop offset="1" stop-color="#FFE59B" stop-opacity="0"/></radialGradient>
    </defs>
    <rect class="stage-background" width="1440" height="900" rx="28" fill="url(#bg)"/>
    <rect width="1440" height="900" rx="28" fill="url(#dots)"/>
    <circle cx="720" cy="455" r="346" fill="url(#golden)"/>
    <g class="orbit-one"><ellipse cx="720" cy="455" rx="510" ry="362"
        fill="none" stroke="#BFD0F1" stroke-width="2" stroke-dasharray="6 15" opacity=".31"/></g>
    <g class="orbit-two"><ellipse cx="720" cy="455" rx="630" ry="434"
        fill="none" stroke="#D5E1FA" stroke-width="1.8" stroke-dasharray="4 19" opacity=".35"/></g>
    <g>{stars()}</g>
    <g class="connections">{''.join(connection)}</g>
    {character(school)}
    <g class="cards">{''.join(cards)}</g>
  </svg>
  <div id="fx-layer" class="fx-layer" aria-hidden="true"></div>
  <div id="toast-area" class="toast-area" role="status" aria-live="polite" aria-atomic="true"></div>
  <div id="finale-layer" class="finale-layer" aria-live="off" aria-hidden="true">
    <div class="finale-halo"></div>
    <div class="finale-inner">
      <div class="finale-kicker">БІЛІМ ДОС · МЫ ВМЕСТЕ!</div>
      <div class="finale-symbol">🌟</div>
      <h2>Спасибо за ваши мысли!</h2>
      <p>Каждый ответ сделал этот урок ярче!</p>
      <div class="finale-lesson">{esc(short(lesson, 80))}</div>
      <div class="finale-signature">💙 Учимся · Делимся · Растём вместе 💛</div>
    </div>
  </div>
</div>
<script id="scene-data" type="application/json">{payload_json}</script>
<script>{js}</script>
</body></html>'''


def render_scene(rows, fresh_ids: set[int], school: str, effects=None, controls=None, lesson="Рефлексия урока", height=700):
    import streamlit.components.v1 as components
    components.html(build_scene(rows, fresh_ids, school, effects=effects,
                                controls=controls, lesson=lesson), height=height, scrolling=False)
