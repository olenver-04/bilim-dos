/* Білім Дос — эффекты появления откликов без внешних JavaScript-библиотек.
   Настройки считываются из effects.json, переданного Python в JSON-сценарии. */
(() => {
  'use strict';
  const source = document.getElementById('scene-data');
  if (!source) return;
  let data;
  try { data = JSON.parse(source.textContent); } catch (_) { return; }
  const options = data.effects || {};
  const stage = document.getElementById('reflection-scene');
  const fx = document.getElementById('fx-layer');
  const toastArea = document.getElementById('toast-area');
  if (!stage || !fx || !toastArea) return;
  // Текст всегда остаётся внутри карточки, даже если имя или ответ длинные.
  document.querySelectorAll('.note-answer, .note-name').forEach(label => {
    try {
      const maxWidth = label.classList.contains('note-answer') ? 169 : 173;
      if (label.getComputedTextLength() > maxWidth) {
        label.setAttribute('textLength', String(maxWidth));
        label.setAttribute('lengthAdjust', 'spacingAndGlyphs');
      }
    } catch (_) { /* SVG measurement is optional on unusual browsers. */ }
  });
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const on = options.enabled !== false && !reducedMotion;
  const boundInt = (value, lo, hi, fallback) =>
    Number.isFinite(value) ? Math.max(lo, Math.min(hi, Math.round(value))) : fallback;
  const duration = boundInt(options.arrival_duration_ms, 450, 2600, 1450);
  const count = boundInt(options.particle_count, 0, 32, 18);
  const maxCelebrations = boundInt(options.max_celebrations_per_refresh, 0, 4, 3);
  const toastDuration = boundInt(options.toast_duration_ms, 1400, 8000, 3600);
  document.documentElement.style.setProperty('--flight-time', duration + 'ms');
  if (!on) return;
  stage.classList.add('motion-on');
  if (options.ambient_animation !== false) stage.classList.add('ambient-on');
  if (options.arrival_animation !== false) stage.classList.add('arrival-on');

  const allFresh = Array.from(document.querySelectorAll('.note.fresh'));
  const cards = maxCelebrations ? allFresh.slice(-maxCelebrations) : []; 
  if (cards.length === 0) return;
  stage.classList.add('celebrating');

  function burst(card, index) {
    if (options.particles_enabled === false || count === 0) return;
    const anchor = card.closest('.note-anchor');
    if (!anchor) return;
    // Координата центра конечной карточки, не зависящая от её CSS-анимации.
    const svg = stage.querySelector('.cluster-svg');
    const matrix = svg && svg.getScreenCTM();
    if (!matrix) return;
    const point = svg.createSVGPoint();
    point.x = Number(card.dataset.x);
    point.y = Number(card.dataset.y);
    const screenPoint = point.matrixTransform(matrix);
    const parent = stage.getBoundingClientRect();
    const x = screenPoint.x - parent.left;
    const y = screenPoint.y - parent.top;
    const color = card.dataset.accent || '#365CD3';
    const palette = [color, '#FFC766', '#98C7FF', '#FF98BD', '#75DABF'];
    const ring = document.createElement('i');
    ring.className = 'fx-ring';
    ring.style.setProperty('--from-x', x + 'px');
    ring.style.setProperty('--from-y', y + 'px');
    ring.style.setProperty('--color', color);
    fx.appendChild(ring);
    ring.addEventListener('animationend', () => ring.remove(), {once: true});
    for (let j = 0; j < count; j++) {
      const p = document.createElement('i');
      p.className = 'fx-particle' + (j % 3 === 0 ? ' round' : '');
      const theta = (j / count) * Math.PI * 2 + index * .43;
      const spread = 32 + (j % 5) * 12;
      p.style.setProperty('--from-x', x + 'px');
      p.style.setProperty('--from-y', y + 'px');
      p.style.setProperty('--vx', (Math.cos(theta) * spread).toFixed(1) + 'px');
      p.style.setProperty('--vy', (Math.sin(theta) * spread - 8).toFixed(1) + 'px');
      p.style.setProperty('--rotation', (j % 2 ? -180 : 180) + 'deg');
      p.style.setProperty('--size', (5 + j % 4) + 'px');
      p.style.setProperty('--color', palette[j % palette.length]);
      p.style.setProperty('--duration', (700 + j % 5 * 90) + 'ms');
      fx.appendChild(p);
      p.addEventListener('animationend', () => p.remove(), {once: true});
    }
  }

  function showToast(card) {
    if (options.toast_enabled === false) return;
    const name = card.dataset.student || 'ученика';
    const toast = document.createElement('div');
    toast.className = 'new-toast';
    const symbol = document.createElement('span');
    symbol.className = 'toast-symbol';
    symbol.textContent = '✨';
    const msg = document.createElement('div');
    msg.className = 'toast-text';
    const headline = document.createElement('b');
    headline.textContent = 'Новая мысль!';
    const author = document.createElement('span');
    author.textContent = name;
    msg.append(headline, author);
    toast.append(symbol, msg);
    toastArea.replaceChildren(toast);
    window.setTimeout(() => toast.classList.add('out'), toastDuration);
    window.setTimeout(() => toast.remove(), toastDuration + 420);
  }

  const toCelebrate = cards.filter(el => el.closest('.note-anchor'));
  toCelebrate.forEach((card, index) => {
    card.style.setProperty('--delay', (index * 190) + 'ms');
    const connection = document.querySelector('.connection.fresh[data-id="' + card.dataset.id + '"]');
    if (connection) connection.style.setProperty('--delay', (index * 190) + 'ms');
    const waitMs = Math.round(duration * .71 + index * 190);
    window.setTimeout(() => burst(card, index), waitMs);
  });
  // При нескольких ответах всплывает только один ненавязчивый тост.
  const newest = toCelebrate.reduce(
    (best, current) => Number(current.dataset.id) > Number(best.dataset.id) ? current : best,
    toCelebrate[0]
  );
  if (newest) window.setTimeout(() => showToast(newest), 580);
})();
