/* Techbase Academy — shared site script (theme, navigation, search palette,
   scroll reveals, progress display). Plain JavaScript, no dependencies. */
(function () {
  'use strict';

  var root = document.documentElement;
  var BASE = document.body.getAttribute('data-root') || '';

  /* ---- storage helpers (storage can throw in private windows) ---- */
  function load(key, fallback) {
    try { var v = localStorage.getItem(key); return v === null ? fallback : JSON.parse(v); } catch (e) { return fallback; }
  }
  function save(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) { /* ignore */ } }
  window.TB = { load: load, save: save };

  /* ---- toast ---- */
  var toastEl = document.getElementById('toast'), toastTimer;
  window.TB.toast = function (msg) {
    if (!toastEl) return;
    toastEl.textContent = msg;
    toastEl.classList.add('is-on');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.classList.remove('is-on'); }, 2600);
  };

  /* ---- theme ---- */
  var themeBtn = document.querySelector('[data-theme-toggle]');
  function effectiveTheme() {
    var t = root.getAttribute('data-theme');
    if (t) return t;
    return window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  if (themeBtn) {
    themeBtn.addEventListener('click', function () {
      var next = effectiveTheme() === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      try { localStorage.setItem('tb-theme', next); } catch (e) { /* ignore */ }
      themeBtn.setAttribute('aria-pressed', next === 'dark' ? 'true' : 'false');
    });
    themeBtn.setAttribute('aria-pressed', effectiveTheme() === 'dark' ? 'true' : 'false');
  }

  /* ---- top bar: shrink + blur on scroll, mobile menu ---- */
  var bar = document.querySelector('.topbar');
  var toTop = document.querySelector('.to-top');
  function onScroll() {
    var y = window.scrollY;
    if (bar) bar.classList.toggle('is-scrolled', y > 8);
    if (toTop) toTop.classList.toggle('is-on', y > 700);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
  if (toTop) toTop.addEventListener('click', function () { window.scrollTo({ top: 0 }); });

  var menuBtn = document.querySelector('[data-menu-toggle]');
  var menu = document.getElementById('site-menu');
  if (menuBtn && menu) {
    var setMenu = function (open) {
      menu.classList.toggle('is-open', open);
      menuBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    };
    menuBtn.addEventListener('click', function () { setMenu(!menu.classList.contains('is-open')); });
    menu.addEventListener('click', function (e) { if (e.target.closest('a')) setMenu(false); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') setMenu(false); });
  }

  /* ---- scroll reveals ---- */
  var reveals = document.querySelectorAll('.reveal');
  if (reveals.length) {
    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); } });
      }, { threshold: 0.08, rootMargin: '0px 0px -6% 0px' });
      reveals.forEach(function (el) { io.observe(el); });
    } else {
      reveals.forEach(function (el) { el.classList.add('is-in'); });
    }
  }

  /* ---- progress (shared between hub, course pages and lessons) ----
     tb:done:<slug>  -> array of lesson file names the learner has finished
     tb:last:<slug>  -> { f: file, t: title, n: number } most recent lesson opened
     tb:last         -> { s: slug, ... } most recent lesson opened anywhere        */
  function doneSet(slug) { return load('tb:done:' + slug, []); }

  function readLegacy(item) {
    /* Interactive lessons keep their phase counter under the key printed in data-key. */
    var key = item.getAttribute('data-key'), total = parseInt(item.getAttribute('data-total'), 10);
    if (!key || !total) return { started: false, done: false };
    var cur;
    try { cur = parseInt(localStorage.getItem(key) || '1', 10); } catch (e) { cur = 1; }
    return { started: cur > 1, done: cur > total };
  }

  var courseRoot = document.querySelector('[data-course-page]');
  if (courseRoot) {
    var slug = courseRoot.getAttribute('data-course-page');
    var items = Array.prototype.slice.call(document.querySelectorAll('.lesson[data-file]'));
    var done = doneSet(slug).slice();
    var changed = false;
    items.forEach(function (it) {
      var f = it.getAttribute('data-file'), legacy = readLegacy(it);
      if (legacy.done && done.indexOf(f) === -1) { done.push(f); changed = true; }
      if (done.indexOf(f) > -1) it.classList.add('is-done');
      else if (legacy.started) it.classList.add('is-started');
    });
    if (changed) save('tb:done:' + slug, done);
    var total = items.length, count = items.filter(function (i) { return i.classList.contains('is-done'); }).length;
    var pc = document.getElementById('progress-card');
    if (pc && count > 0) {
      pc.classList.add('has-progress');
      pc.querySelector('.bar > i').style.width = Math.round(count / total * 100) + '%';
      pc.querySelector('[data-progress-text]').textContent = count + ' of ' + total + ' complete';
    }
    var cont = document.getElementById('continue-btn');
    var last = load('tb:last:' + slug, null);
    if (cont) {
      var target = last && items.some(function (i) { return i.getAttribute('data-file') === last.f; }) ? last : null;
      if (!target) {
        var firstOpen = items.filter(function (i) { return !i.classList.contains('is-done'); })[0];
        if (firstOpen && count > 0) target = { f: firstOpen.getAttribute('data-file'), n: firstOpen.getAttribute('data-num') };
      }
      if (target) {
        cont.href = 'lessons/' + target.f;
        cont.querySelector('[data-label]').textContent = 'Continue with ' + (target.n || 'lesson');
        cont.hidden = false;
      }
    }

    /* filter */
    var input = document.getElementById('lesson-filter');
    var chipBtns = Array.prototype.slice.call(document.querySelectorAll('[data-level-chip]'));
    var empty = document.getElementById('lesson-empty');
    var level = 'all';
    var apply = function () {
      var q = (input ? input.value : '').trim().toLowerCase(), shown = 0;
      items.forEach(function (it) {
        var ok = (!q || it.getAttribute('data-search').indexOf(q) > -1) && (level === 'all' || it.getAttribute('data-level') === level);
        it.parentElement.hidden = !ok;
        if (ok) shown++;
      });
      Array.prototype.forEach.call(document.querySelectorAll('[data-phase]'), function (ph) {
        ph.hidden = !ph.querySelector('li:not([hidden])');
      });
      if (empty) empty.classList.toggle('is-visible', shown === 0);
    };
    if (input) input.addEventListener('input', apply);
    chipBtns.forEach(function (b) {
      b.addEventListener('click', function () {
        level = b.getAttribute('data-level-chip');
        chipBtns.forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
        apply();
      });
    });
  }

  /* hub: per-course progress bars + "continue" link */
  Array.prototype.forEach.call(document.querySelectorAll('[data-hub-card]'), function (card) {
    var s = card.getAttribute('data-hub-card'), n = parseInt(card.getAttribute('data-count'), 10);
    var c = doneSet(s).length;
    if (c > 0 && n) {
      card.classList.add('has-progress');
      card.querySelector('.bar > i').style.width = Math.min(100, Math.round(c / n * 100)) + '%';
      var t = card.querySelector('[data-progress-text]');
      if (t) t.textContent = c + ' of ' + n + ' done';
    }
  });
  var gl = document.getElementById('continue-global');
  if (gl) {
    var lastAny = load('tb:last', null);
    if (lastAny && lastAny.u) {
      gl.href = lastAny.u;
      gl.querySelector('[data-label]').textContent = 'Continue: ' + lastAny.t;
      gl.hidden = false;
    }
  }

  /* ---- command palette (Ctrl/Cmd + K, or "/") ---- */
  var dlg = document.getElementById('palette');
  if (dlg && typeof dlg.showModal === 'function') {
    var input2 = dlg.querySelector('input'), list = dlg.querySelector('.palette-list'), index = null, results = [], sel = 0;
    var esc = function (s) { return String(s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
    var fetchIndex = function () {
      if (index) return Promise.resolve(index);
      return fetch(BASE + 'assets/data/search.json').then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
        .then(function (d) { index = d; return d; });
    };
    var score = function (item, terms) {
      var hay = (item.t + ' ' + (item.d || '') + ' ' + item.cs + ' ' + item.n).toLowerCase(), s = 0;
      for (var i = 0; i < terms.length; i++) {
        var p = hay.indexOf(terms[i]);
        if (p < 0) return 0;
        s += (item.t.toLowerCase().indexOf(terms[i]) > -1 ? 6 : 2) + (p === 0 ? 2 : 0);
      }
      return s;
    };
    var render = function () {
      if (!results.length) {
        list.innerHTML = '<li class="palette-empty">' + (index ? 'No lessons match that. Try a topic like "flexbox" or "loops".' : 'Loading lessons…') + '</li>';
        return;
      }
      list.innerHTML = results.map(function (r, i) {
        return '<li><a role="option" href="' + BASE + esc(r.u) + '" class="c-' + esc(r.c) + '" aria-selected="' + (i === sel) + '" data-i="' + i + '">' +
          '<span class="tile" style="width:2.2rem;height:2.2rem;font:700 .72rem var(--font-mono)">' + esc(r.n) + '</span>' +
          '<span><b>' + esc(r.t) + '</b><small>' + esc(r.cs) + (r.d ? ' · ' + esc(r.d) : '') + '</small></span></a></li>';
      }).join('');
    };
    var run = function () {
      var q = input2.value.trim().toLowerCase();
      if (!index) { results = []; render(); return; }
      var terms = q.split(/\s+/).filter(Boolean);
      results = (terms.length ? index.map(function (it) { return { it: it, s: score(it, terms) }; }).filter(function (x) { return x.s > 0; })
        .sort(function (a, b) { return b.s - a.s; }).map(function (x) { return x.it; }) : index.filter(function (it) { return /^0*1$/.test(it.n); })).slice(0, 8);
      sel = 0; render();
    };
    var open = function () {
      if (!dlg.open) dlg.showModal();
      input2.value = ''; results = []; render();
      fetchIndex().then(run).catch(function () { list.innerHTML = '<li class="palette-empty">Search is unavailable offline. Browse the courses instead.</li>'; });
      input2.focus();
    };
    input2.addEventListener('input', run);
    dlg.addEventListener('click', function (e) { if (e.target === dlg) dlg.close(); });
    dlg.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault();
        if (!results.length) return;
        sel = (sel + (e.key === 'ArrowDown' ? 1 : -1) + results.length) % results.length; render();
        var cur = list.querySelector('[aria-selected="true"]'); if (cur) cur.scrollIntoView({ block: 'nearest' });
      } else if (e.key === 'Enter' && results[sel]) {
        e.preventDefault(); window.location.href = BASE + results[sel].u;
      }
    });
    document.addEventListener('keydown', function (e) {
      var typing = /^(INPUT|TEXTAREA|SELECT)$/.test((document.activeElement || {}).tagName || '');
      if ((e.key === 'k' || e.key === 'K') && (e.ctrlKey || e.metaKey)) { e.preventDefault(); open(); }
      else if (e.key === '/' && !typing && !dlg.open) { e.preventDefault(); open(); }
    });
    Array.prototype.forEach.call(document.querySelectorAll('[data-open-search]'), function (b) { b.addEventListener('click', open); });
  } else {
    Array.prototype.forEach.call(document.querySelectorAll('[data-open-search]'), function (b) { b.hidden = true; });
  }
})();
