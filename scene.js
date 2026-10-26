/* BILIM DOS 5.0 — lightweight cinematic stage without third-party JS libs.
   Server timestamp synchronizes a finale across iframe refreshes and projectors. */
(() => {
  'use strict';
  const source = document.getElementById('scene-data');
  if (!source) return;
  let payload;
  try { payload = JSON.parse(source.textContent); } catch (_) { return; }
  const settings = payload.effects || {};
  const controls = payload.controls || {};
  const stage = document.getElementById('reflection-scene');
  const fxLayer = document.getElementById('fx-layer');
  const toastArea = document.getElementById('toast-area');
  const finaleLayer = document.getElementById('finale-layer');
  const svg = stage && stage.querySelector('.cluster-svg');
  if (!stage || !fxLayer || !toastArea || !svg || !finaleLayer) return;

  const bool = (key, fallback = true) =>
    typeof controls[key] === 'boolean' ? controls[key] : fallback;
  const number = (value, low, high, fallback) =>
    Number.isFinite(value) ? Math.max(low, Math.min(high, Math.round(value))) : fallback;
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const motion = settings.enabled !== false && bool('fx_enabled') && !prefersReducedMotion;
  const mascot = bool('fx_mascot');
  const arrival = bool('fx_arrival') && settings.arrival_animation !== false;
  const particles = bool('fx_particles') && settings.particles_enabled !== false;
  const toast = bool('fx_toast') && settings.toast_enabled !== false;
  const theme = ['sky', 'lavender', 'mint'].includes(controls.fx_theme) ? controls.fx_theme : 'sky';
  stage.dataset.theme = theme;
  const background = svg.querySelector('.stage-background');
  if (background) background.setAttribute('fill', theme === 'sky' ? 'url(#bg)' : 'url(#bg-' + theme + ')');

  const duration = number(controls.fx_arrival_duration_ms ?? settings.arrival_duration_ms, 500, 2400, 1450);
  const count = number(controls.fx_particle_count ?? settings.particle_count, 0, 32, 18);
  const maxCelebrations = number(settings.max_celebrations_per_refresh, 0, 4, 3);
  const toastDuration = number(settings.toast_duration_ms, 1400, 8000, 3600);
  const finaleDuration = number(settings.finale_duration_ms, 12000, 30000, 18000);
  stage.style.setProperty('--flight-time', duration + 'ms');
  stage.style.setProperty('--finale-duration', finaleDuration + 'ms');

  // SVG labels retain their whole tooltip; visible words fit even on narrow screens.
  document.querySelectorAll('.note-answer, .note-name').forEach((label) => {
    try {
      const limit = label.classList.contains('note-answer') ? 170 : 172;
      if (label.getComputedTextLength() > limit) {
        label.setAttribute('textLength', String(limit));
        label.setAttribute('lengthAdjust', 'spacingAndGlyphs');
      }
    } catch (_) { /* static SVG is still usable */ }
  });

  // Trust the server clock, not the device clock (classroom tablets can be unsynced).
  const serverNow = Date.parse(payload.server_now || '');
  const ageOf = (time) => {
    if (!time || !Number.isFinite(serverNow)) return Infinity;
    const eventTime = Date.parse(time);
    if (!Number.isFinite(eventTime)) return Infinity;
    return Math.max(0, serverNow - eventTime);
  };
  const showAge = ageOf(controls.show_started_at);
  const finaleVisible = bool('fx_finale') && showAge < finaleDuration;
  if (motion) {
    stage.classList.add('motion-on');
    if (settings.ambient_animation !== false && bool('fx_ambient')) stage.classList.add('ambient-on');
    if (arrival) stage.classList.add('arrival-on');
    if (mascot) stage.classList.add('mascot-on');
  }

  function useSpeech(text) {
    if (!mascot) return;
    const label = document.getElementById('mascot-text');
    if (label) label.textContent = text;
    stage.classList.add('receiving');
  }

  function relativeSVGPoint(x, y) {
    const matrix = svg.getScreenCTM();
    if (!matrix) return null;
    const point = svg.createSVGPoint();
    point.x = x;
    point.y = y;
    const converted = point.matrixTransform(matrix);
    const rect = stage.getBoundingClientRect();
    return { x: converted.x - rect.left, y: converted.y - rect.top };
  }

  function burstAt(x, y, accent = '#365CD3', n = count) {
    if (!motion || !particles || !n) return;
    const position = relativeSVGPoint(x, y);
    if (!position) return;
    const ring = document.createElement('i');
    ring.className = 'fx-ring';
    ring.style.setProperty('--from-x', position.x + 'px');
    ring.style.setProperty('--from-y', position.y + 'px');
    ring.style.setProperty('--color', accent);
    fxLayer.appendChild(ring);
    ring.addEventListener('animationend', () => ring.remove(), {once:true});
    const palette = [accent, '#FFD377', '#A6C8FF', '#FF9FB8', '#9BE8CE'];
    for (let i = 0; i < n; i++) {
      const particle = document.createElement('i');
      particle.className = 'fx-particle' + (i % 3 === 0 ? ' round' : '');
      const theta = i * 2.399963229728653;
      const radius = 32 + i % 6 * 13;
      particle.style.setProperty('--from-x', position.x + 'px');
      particle.style.setProperty('--from-y', position.y + 'px');
      particle.style.setProperty('--vx', (Math.cos(theta) * radius).toFixed(1) + 'px');
      particle.style.setProperty('--vy', (Math.sin(theta) * radius - 8).toFixed(1) + 'px');
      particle.style.setProperty('--rotation', (i % 2 ? -200 : 180) + 'deg');
      particle.style.setProperty('--size', (5 + i % 5) + 'px');
      particle.style.setProperty('--color', palette[i % palette.length]);
      particle.style.setProperty('--duration', (680 + i % 4 * 110) + 'ms');
      fxLayer.appendChild(particle);
      particle.addEventListener('animationend', () => particle.remove(), {once:true});
    }
  }

  function notification(heading, name) {
    if (!toast || !motion) return;
    const element = document.createElement('div');
    element.className = 'new-toast';
    const icon = document.createElement('span');
    icon.className = 'toast-symbol';
    icon.textContent = '✨';
    const words = document.createElement('div');
    words.className = 'toast-text';
    const title = document.createElement('b');
    title.textContent = heading;
    const student = document.createElement('span');
    student.textContent = name;
    words.append(title, student);
    element.append(icon, words);
    toastArea.replaceChildren(element);
    window.setTimeout(() => element.classList.add('out'), toastDuration);
    window.setTimeout(() => element.remove(), toastDuration + 450);
  }

  function prepareFinale(elapsed) {
    const sync = -Math.round(elapsed) + 'ms';
    stage.style.setProperty('--finale-offset', sync);
    if (!motion) {
      stage.classList.add('finale-static');
      return;
    }
    stage.classList.add('finale-active');
    useSpeech('Какой класс!');
    const colors = ['#FFD375','#FFFFFF','#FF9BC5','#94DAFF','#96E5C2','#C5B6FF'];
    // Recreating the iframe does not replay the show: negative animation delay
    // carries confetti and celebration back to the actual UTC event timeline.
    for (let i = 0; i < 66; i++) {
      const particle = document.createElement('i');
      particle.className = 'finale-confetti';
      particle.style.setProperty('--confetti-x', ((i * 47.37) % 100).toFixed(1) + '%');
      particle.style.setProperty('--confetti-shift', (Math.sin(i * 1.72) * 210).toFixed(0) + 'px');
      particle.style.setProperty('--confetti-spin', (i % 2 ? 600 : -720) + 'deg');
      particle.style.setProperty('--confetti-phase', (-1 * ((i * 157) % 2800)) + 'ms');
      particle.style.setProperty('--confetti-color', colors[i % colors.length]);
      particle.style.setProperty('--confetti-width', (6 + i % 4 * 2) + 'px');
      particle.style.setProperty('--confetti-height', (10 + i % 5 * 3) + 'px');
      finaleLayer.appendChild(particle);
    }
    const label = finaleLayer.querySelector('h2');
    if (label) label.setAttribute('aria-label', 'Спасибо за ваши мысли!');
  }

  if (finaleVisible) {
    prepareFinale(showAge);
    return;
  }
  if (!motion) return;

  const fresh = Array.from(document.querySelectorAll('.note.fresh'));
  const recentCards = maxCelebrations ? fresh.slice(-maxCelebrations) : [];
  const testAge = ageOf(controls.demo_started_at);
  const runDemo = testAge < 4200;

  if (fresh.length) {
    stage.classList.add('receiving', 'celebrating');
    useSpeech(['Отличная мысль!', 'Вот это да!', 'Ты молодец!'][fresh.length % 3]);
  }
  if (recentCards.length) {
    recentCards.forEach((card, index) => {
      const delay = index * 180;
      card.style.setProperty('--delay', delay + 'ms');
      const connection = document.querySelector('.connection.fresh[data-id="' + card.dataset.id + '"]');
      if (connection) connection.style.setProperty('--delay', delay + 'ms');
      const x = Number(card.dataset.x);
      const y = Number(card.dataset.y);
      const wait = arrival ? Math.round(duration * 0.76 + delay) : 180 + delay;
      window.setTimeout(() => burstAt(x, y, card.dataset.accent || '#365CD3'), wait);
    });
    const latest = recentCards.reduce((a,b) => Number(a.dataset.id) > Number(b.dataset.id) ? a : b);
    window.setTimeout(() => notification('Новая мысль!', latest.dataset.student || 'Наш ученик'), 380);
  }
  if (runDemo && !fresh.length) {
    stage.classList.add('receiving', 'celebrating');
    useSpeech('Ура! Всё работает!');
    // Demo is visibly different from student messages, adds no database record.
    window.setTimeout(() => burstAt(720, 345, '#FFB64E', Math.min(26, count)), 100);
    window.setTimeout(() => notification('Пробный эффект', 'Пульт учителя'), 280);
  }
})();
