/* Techbase Academy — shared site script (theme, navigation, search palette,
   scroll reveals, progress display). Plain JavaScript, no dependencies. */
(function () {
  'use strict';

  var root = document.documentElement;
  var rawBase = document.body.getAttribute('data-root') || '';
  var BASE = /^(?:(?:\.\.\/)*|\/)$/.test(rawBase) ? rawBase : '';   // only '', '../' steps or '/' are ever valid
  var LESSON_URL = /^[a-z0-9-]+\/lessons\/[a-z0-9_.-]+$/i;

  /* ---- storage helpers (storage can throw in private windows) ---- */
  function load(key, fallback) {
    try { var v = localStorage.getItem(key); return v === null ? fallback : JSON.parse(v); } catch (e) { return fallback; }
  }
  function touch() { try { document.dispatchEvent(new CustomEvent('tb:progress')); } catch (e) { /* ignore */ } }
  function save(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) { /* ignore */ } if (key.indexOf('tb:') === 0) touch(); }
  window.TB = { load: load, save: save, touch: touch };
  /* tiny DOM builder: text always goes in as text, never as markup */
  function h(tag, attrs, kids) {
    var n = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) { if (attrs[k] === true) n.setAttribute(k, ''); else if (attrs[k] !== false && attrs[k] != null) n.setAttribute(k, attrs[k]); });
    (kids || []).forEach(function (c) { n.appendChild(typeof c === 'string' ? document.createTextNode(c) : c); });
    return n;
  }
  function icon(name) {
    var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('class', 'icon'); svg.setAttribute('aria-hidden', 'true');
    var use = document.createElementNS('http://www.w3.org/2000/svg', 'use'); use.setAttribute('href', '#i-' + name);
    svg.appendChild(use); return svg;
  }
  window.TB.h = h;

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
    var paintCourse = function () {
    var done = doneSet(slug).slice();
    var changed = false;
    items.forEach(function (it) {
      var f = it.getAttribute('data-file'), legacy = readLegacy(it);
      it.classList.remove('is-done', 'is-started');
      if (legacy.done && done.indexOf(f) === -1) { done.push(f); changed = true; }
      if (done.indexOf(f) > -1) it.classList.add('is-done');
      else if (legacy.started) it.classList.add('is-started');
    });
    if (changed) { try { localStorage.setItem('tb:done:' + slug, JSON.stringify(done)); } catch (e) { /* ignore */ } }
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
    };
    paintCourse();
    window.addEventListener('tb:repaint', paintCourse);

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
  var paintHub = function () {
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
    if (lastAny && typeof lastAny.u === 'string' && LESSON_URL.test(lastAny.u)) {
      gl.href = BASE + lastAny.u;
      gl.querySelector('[data-label]').textContent = 'Continue: ' + lastAny.t;
      gl.hidden = false;
    }
  }
  };
  paintHub();
  window.addEventListener('tb:repaint', paintHub);

  /* ---- command palette (Ctrl/Cmd + K, or "/") ---- */
  var dlg = document.getElementById('palette');
  if (dlg && typeof dlg.showModal === 'function') {
    var input2 = dlg.querySelector('input'), list = dlg.querySelector('.palette-list'), index = null, results = [], sel = 0;
    var fetchIndex = function () {
      if (index) return Promise.resolve(index);
      return fetch(BASE + 'assets/data/search.json').then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
        .then(function (d) { index = d; return d; });
    };
    var score = function (item, terms) {
      var hay = (item.t + ' ' + (item.d || '') + ' ' + item.cs + ' ' + (item.n || '')).toLowerCase(), s = 0;
      for (var i = 0; i < terms.length; i++) {
        var p = hay.indexOf(terms[i]);
        if (p < 0) return 0;
        s += (item.t.toLowerCase().indexOf(terms[i]) > -1 ? 6 : 2) + (p === 0 ? 2 : 0);
      }
      return s;
    };
    var say = function (msg) { while (list.firstChild) list.removeChild(list.firstChild); list.appendChild(h('li', { 'class': 'palette-empty' }, [msg])); };
    var render = function () {
      if (!results.length) { say(index ? 'Nothing matches that. Try a topic like "flexbox", or a word like "robotics" or "contact".' : 'Loading lessons…'); return; }
      var kinds = { lesson: 'Lesson', course: 'Course', page: 'Page', faq: 'FAQ', post: 'Article', event: 'Programme' };
      while (list.firstChild) list.removeChild(list.firstChild);
      results.forEach(function (r, i) {
        var k = kinds[r.k || 'lesson'] ? (r.k || 'lesson') : 'page';
        var tile = h('span', { 'class': 'tile k-' + k, style: 'font:700 .72rem var(--font-mono)' }, []);
        if (k === 'lesson' || k === 'course') tile.appendChild(document.createTextNode(String(r.n || '·')));
        else tile.appendChild(icon(k === 'page' ? 'arrow' : k === 'faq' ? 'message' : 'book'));
        var cls = /^[a-z0-9-]+$/.test(String(r.c)) ? r.c : 'site';
        var href = /^[a-z0-9\/_.#-]+$/i.test(String(r.u)) ? BASE + r.u : BASE + 'index.html';
        var a = h('a', { role: 'option', href: href, 'class': 'c-' + cls, 'aria-selected': String(i === sel), 'data-i': String(i) }, [tile,
          h('span', {}, [h('b', {}, [String(r.t)]), h('small', {}, [String(r.cs) + (r.d ? ' \u00b7 ' + r.d : '')])]),
          h('span', { 'class': 'kind' }, [kinds[k]])]);
        list.appendChild(h('li', {}, [a]));
      });
    };
    var run = function () {
      var q = input2.value.trim().toLowerCase();
      if (!index) { results = []; render(); return; }
      var terms = q.split(/\s+/).filter(Boolean);
      results = (terms.length ? index.map(function (it) { return { it: it, s: score(it, terms) }; }).filter(function (x) { return x.s > 0; })
        .sort(function (a, b) { return b.s - a.s; }).map(function (x) { return x.it; }) : index.filter(function (it) { return it.k === 'page'; })).slice(0, 8);
      sel = 0; render();
    };
    var open = function () {
      if (!dlg.open) dlg.showModal();
      input2.value = ''; results = []; render();
      fetchIndex().then(run).catch(function () { say('Search is unavailable offline. Browse the courses instead.'); });
      input2.focus();
    };
    input2.addEventListener('input', run);
    dlg.addEventListener('click', function (e) { if (e.target === dlg) dlg.close(); });
    dlg.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { e.preventDefault(); dlg.close(); return; }
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

  /* ---- service worker (offline reading of pages you have opened) ---- */
  if ('serviceWorker' in navigator && location.protocol === 'https:') {
    window.addEventListener('load', function () { navigator.serviceWorker.register('/sw.js').catch(function () { /* ignore */ }); });
  }
  var reload = document.querySelector('[data-reload]');
  if (reload) reload.addEventListener('click', function () { location.reload(); });

  /* ---- accounts: the Firebase code is a separate file, loaded only when it is needed ---- */
  var accountsOn = document.body.getAttribute('data-accounts') === 'on';
  var FLAG = 'tb:signedin';
  var hint = load(FLAG, null);                    // { n: name } while a session is (probably) active
  var path = location.pathname;
  var needsAuth = accountsOn && (!!hint || /\/(login|account)\//.test(path) || !!document.querySelector('[data-needs-auth]'));
  var resolveReady, ready = new Promise(function (r) { resolveReady = r; });
  window.TB.authReady = ready;
  window.TB.user = null;
  var loadAuth = function () {
    if (window.TB.authLoading) return ready;
    window.TB.authLoading = true;
    var s = document.createElement('script');
    var ver = document.body.getAttribute('data-v') || '';
    s.src = BASE + 'assets/js/auth.js' + (/^[a-f0-9]{1,16}$/.test(ver) ? '?v=' + ver : '');
    s.onerror = function () { window.TB.authLoading = false; resolveReady(null); announce(null); };
    document.head.appendChild(s);
    return ready;
  };
  window.TB.loadAuth = loadAuth;

  function initial(name) { return (String(name || '?').trim().charAt(0) || '?').toUpperCase(); }
  function acctNode(name, email) {
    var wrap = h('div', { 'class': 'acct' });
    wrap.appendChild(h('button', { type: 'button', 'class': 'acct-btn', 'aria-haspopup': 'true', 'aria-expanded': 'false', 'data-acct-toggle': true }, [
      h('span', { 'class': 'avatar', 'aria-hidden': 'true' }, [initial(name)]),
      h('span', { 'class': 'nm' }, [String(name || 'Account').split(' ')[0]]), icon('chev-down')]));
    wrap.appendChild(h('div', { 'class': 'acct-pop', hidden: true }, [
      h('div', { 'class': 'who' }, [h('b', {}, [name || 'Learner']), h('small', {}, [email || ''])]),
      h('a', { href: BASE + 'learn/index.html' }, ['My courses']),
      h('a', { href: BASE + 'account/index.html' }, ['Account']),
      h('button', { type: 'button', 'data-signout': true }, ['Sign out'])]));
    return wrap;
  }
  function fill(node, kids) { while (node.firstChild) node.removeChild(node.firstChild); kids.forEach(function (k) { node.appendChild(k); }); }

  function renderAuth(user, pending) {
    var slot = document.querySelector('[data-auth-slot]');
    var menuSlot = document.querySelector('[data-menu-auth]');
    if (user || pending) {
      var nm = user ? (user.displayName || (user.email || '').split('@')[0]) : '';
      if (slot) fill(slot, [acctNode(nm, user && user.email)]);
      if (menuSlot) fill(menuSlot, [h('a', { href: BASE + 'account/index.html' }, ['Account']), h('button', { type: 'button', 'class': 'btn btn--sm btn--ghost', 'data-signout': true }, ['Sign out'])]);
    } else if (accountsOn) {
      if (slot) fill(slot, [h('a', { 'class': 'nav-login', href: BASE + 'login/index.html' }, ['Log in']), h('a', { 'class': 'btn btn--sm', href: BASE + 'login/index.html#signup' }, ['Create account'])]);
      if (menuSlot) fill(menuSlot, [h('a', { href: BASE + 'login/index.html' }, ['Log in']), h('a', { 'class': 'btn btn--sm', href: BASE + 'login/index.html#signup' }, ['Create free account'])]);
    }
    Array.prototype.forEach.call(document.querySelectorAll('[data-when-signed-in]'), function (el) { el.hidden = !user; });
    Array.prototype.forEach.call(document.querySelectorAll('[data-when-signed-out]'), function (el) { el.hidden = !!user; });
  }
  document.addEventListener('click', function (e) {
    var t = e.target.closest('[data-acct-toggle]');
    var pop = document.querySelector('.acct-pop');
    if (t && pop) { var open = pop.hidden; pop.hidden = !open; t.setAttribute('aria-expanded', open ? 'true' : 'false'); return; }
    if (pop && !pop.hidden && !e.target.closest('.acct-pop')) { pop.hidden = true; var b = document.querySelector('[data-acct-toggle]'); if (b) b.setAttribute('aria-expanded', 'false'); }
    if (e.target.closest('[data-signout]')) {
      e.preventDefault();
      loadAuth().then(function () { return window.TB.auth && window.TB.auth.signOut(); }).then(function () { TB.toast('Signed out.'); });
    }
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { var pop = document.querySelector('.acct-pop'); if (pop && !pop.hidden) { pop.hidden = true; var b = document.querySelector('[data-acct-toggle]'); if (b) { b.setAttribute('aria-expanded', 'false'); b.focus(); } } }
  });

  /* soft lesson gate: UI only (see docs/CUSTOMIZING.md for what that means) */
  var FREE_N = parseInt(document.body.getAttribute('data-free') || '1', 10);
  function applyGate(user) {
    var gate = document.body.getAttribute('data-gate');
    if (accountsOn && gate === 'locked') {
      var wall = document.getElementById('gate-wall');
      if (!user && !wall) {
        document.body.classList.add('is-gated');
        var host = document.querySelector('#lesson-main'), layout = host && host.closest('.lesson-layout, .project-layout');
        if (layout) {
          var w = h('div', { id: 'gate-wall', 'class': 'gate-wall' }, [
            h('h2', {}, ['Create a free account to keep going']),
            h('p', {}, ['The first lesson of every course is open to everyone. A free account unlocks the rest and saves your progress on every device. No card needed.']),
            h('div', { 'class': 'hero-actions' }, [
              h('a', { 'class': 'btn btn--lg', href: BASE + 'login/index.html#signup' }, ['Create free account']),
              h('a', { 'class': 'btn btn--lg btn--ghost', href: BASE + 'login/index.html' }, ['Log in'])])]);
          layout.parentNode.insertBefore(w, layout.nextSibling);
        }
      } else if (user && wall) { wall.remove(); document.body.classList.remove('is-gated'); }
    }
    var courseItems = document.querySelectorAll('.lessons .lesson[data-file]');
    if (accountsOn && courseItems.length) {
      Array.prototype.forEach.call(courseItems, function (it, i) {
        it.classList.toggle('is-locked', !user && i >= FREE_N);
        var b = it.querySelector('.lock-badge');
        if (!user && i >= FREE_N && !b) { var sp = h('span', { 'class': 'lock-badge' }, [icon('lock'), ' Free account']); var holder = it.querySelector('small'); if (holder) holder.appendChild(sp); }
        else if ((user || i < FREE_N) && b) b.remove();
      });
    }
  }
  function announce(user) {
    window.TB.user = user;
    renderAuth(user, false);
    applyGate(user);
    try { document.dispatchEvent(new CustomEvent('tb:auth', { detail: { user: user } })); } catch (e) { /* ignore */ }
  }
  window.TB.announceAuth = function (user) {
    if (user) save(FLAG, 1); else { try { localStorage.removeItem(FLAG); } catch (e) { /* ignore */ } }
    announce(user); resolveReady(user);
  };
  if (hint && accountsOn) renderAuth(null, true);
  if (needsAuth) loadAuth();
  else { announce(null); resolveReady(null); }
})();
