/* Techbase Academy — lesson interactivity.
   Interactive lessons keep the original progress keys (data-key on <main>) so
   learners do not lose progress. Without JavaScript every phase stays visible. */
(function () {
  'use strict';
  var main = document.getElementById('lesson-main');
  if (!main) return;
  var TB = window.TB || { load: function (k, f) { return f; }, save: function () {}, toast: function () {} };
  var slug = main.getAttribute('data-course'), file = main.getAttribute('data-file');
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var behavior = reduce ? 'auto' : 'smooth';

  /* remember where the learner is */
  var rec = { f: file, t: main.getAttribute('data-title'), n: main.getAttribute('data-num') };
  TB.save('tb:last:' + slug, rec);
  TB.save('tb:last', { s: slug, u: main.getAttribute('data-url'), t: rec.t, at: Date.now() });

  function markDone() {
    var d = TB.load('tb:done:' + slug, []);
    if (d.indexOf(file) === -1) { d.push(file); TB.save('tb:done:' + slug, d); }
  }

  /* ---------- project lessons: mark as done ---------- */
  var mark = document.getElementById('mark-done');
  if (mark) {
    var paint = function () {
      var on = TB.load('tb:done:' + slug, []).indexOf(file) > -1;
      mark.setAttribute('aria-pressed', on ? 'true' : 'false');
      mark.querySelector('[data-label]').textContent = on ? 'Marked as done' : 'Mark as done';
    };
    mark.addEventListener('click', function () {
      var d = TB.load('tb:done:' + slug, []), i = d.indexOf(file);
      if (i > -1) d.splice(i, 1); else d.push(file);
      TB.save('tb:done:' + slug, d); paint();
      if (i === -1) TB.toast('Nice work. Project saved as done.');
    });
    paint();
  }

  /* ---------- interactive lessons: phases ---------- */
  var total = parseInt(main.getAttribute('data-total'), 10), key = main.getAttribute('data-key');
  var phases = total ? Array.prototype.slice.call(main.querySelectorAll('.phase')) : [];
  var bar = document.getElementById('lesson-bar');
  var railLinks = Array.prototype.slice.call(document.querySelectorAll('.rail a'));
  var cur = 1;
  if (total && key) { try { cur = parseInt(localStorage.getItem(key) || '1', 10) || 1; } catch (e) { cur = 1; } }

  function scrollTo(el) { if (el) setTimeout(function () { el.scrollIntoView({ behavior: behavior, block: 'start' }); }, 160); }
  function paintBar(p) { if (bar) bar.style.width = (p !== undefined ? p : Math.round((cur - 1) / total * 95)) + '%'; }
  function paintRail() {
    railLinks.forEach(function (a, i) {
      var n = i + 1;
      a.classList.toggle('is-done', n < cur);
      a.classList.toggle('is-locked', n > cur && cur <= total);
    });
  }
  function unlock(n, doScroll) {
    var el = document.getElementById('phase' + n);
    if (!el) return;
    el.classList.remove('is-locked');
    if (doScroll) scrollTo(el);
  }
  function showBuild() {
    ['build-it', 'gh-steps', 'session-end'].forEach(function (id) {
      var el = document.getElementById(id);
      if (!el) return;
      if (id === 'build-it') el.classList.add('visible');
    });
  }

  if (total) {
    phases.forEach(function (p, i) { if (i + 1 > cur) p.classList.add('is-locked'); });
    for (var i = 1; i < cur && i <= total; i++) {
      var c = document.getElementById('chk' + i);
      if (c) { c.classList.add('done'); c.textContent = '✓'; }
    }
    if (cur > total) showBuild();
    paintBar(cur > total ? 100 : undefined);
    paintRail();
  }

  function unlockNext(n) {
    var c = document.getElementById('chk' + n);
    if (c) { c.classList.add('done'); c.textContent = '✓'; }
    try { localStorage.setItem(key, String(n + 1)); } catch (e) { /* ignore */ } TB.touch();
    cur = n + 1;
    paintRail();
    if (n >= total) {
      showBuild(); paintBar(100); markDone();
      TB.toast('All phases complete. Time to build.');
      var b = document.getElementById('build-it');
      scrollTo(b);
      if (!reduce) setTimeout(confetti, 500);
    } else {
      unlock(n + 1, true); paintBar();
      TB.toast(['Phase complete', 'Keep going', 'Nice work', 'Nailed it'][n % 4]);
    }
  }

  /* ---------- event delegation for every data-action in lesson bodies ---------- */
  document.addEventListener('click', function (e) {
    var el = e.target.closest('[data-action]');
    if (!el) return;
    var act = el.getAttribute('data-action');
    if (act === 'unlock') unlockNext(parseInt(el.getAttribute('data-n'), 10));
    else if (act === 'copy') copy(el);
    else if (act === 'alert') window.alert(el.getAttribute('data-msg') || '');
    else if (act === 'reveal') {
      var wrap = el.nextElementSibling; if (!wrap) return;
      var open = wrap.classList.toggle('open');
      el.textContent = open ? el.getAttribute('data-hide') : el.getAttribute('data-show');
      el.setAttribute('aria-expanded', open ? 'true' : 'false');
    } else if (act === 'github') {
      var g = document.getElementById('gh-steps');
      if (g) { g.classList.add('visible'); var bd = g.querySelector('.gh-bd'); if (bd) bd.classList.add('open'); scrollTo(g); }
    } else if (act === 'toggle-gh') {
      var body = el.nextElementSibling; if (body) { var o = body.classList.toggle('open'); el.classList.toggle('is-open', o); }
    } else if (act === 'finish') {
      var s = document.getElementById('session-end');
      if (s) { s.classList.add('visible'); markDone(); scrollTo(s); }
    } else if (act === 'download') {
      var a = document.createElement('a');
      a.href = 'data:text/html;charset=utf-8,' + encodeURIComponent(el.getAttribute('data-starter') || '');
      a.download = el.getAttribute('data-filename') || 'starter.html';
      document.body.appendChild(a); a.click(); a.remove();
    }
  });

  function copy(btn) {
    var wrap = btn.closest('.v2-code-wrap'), code = wrap && wrap.querySelector('code');
    if (!code) return;
    var text = code.innerText;
    var ok = function () {
      var label = btn.querySelector('[data-label]') || btn;
      var old = label.textContent;
      label.textContent = 'Copied'; btn.classList.add('copied');
      setTimeout(function () { label.textContent = old; btn.classList.remove('copied'); }, 1800);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(ok, fallback);
    else fallback();
    function fallback() {
      var ta = document.createElement('textarea'); ta.value = text; ta.setAttribute('readonly', '');
      ta.style.position = 'fixed'; ta.style.opacity = '0'; document.body.appendChild(ta); ta.select();
      try { if (document.execCommand('copy')) ok(); } catch (e) { /* ignore */ }
      ta.remove();
    }
  }

  /* ---------- contents rail: highlight the phase in view ---------- */
  if (railLinks.length && 'IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        var id = en.target.id;
        railLinks.forEach(function (a) { a.classList.toggle('is-active', a.getAttribute('href') === '#' + id); });
      });
    }, { rootMargin: '-20% 0px -65% 0px' });
    phases.forEach(function (p) { io.observe(p); });
  }

  /* ---------- confetti (skipped for reduced motion) ---------- */
  function confetti() {
    var cv = document.getElementById('confetti');
    if (!cv) return;
    var ctx = cv.getContext('2d');
    cv.style.display = 'block'; cv.width = innerWidth; cv.height = innerHeight;
    var colors = ['#2457e6', '#f5a524', '#0f8a5f', '#e34f26', '#7c3aed', '#e11d48'];
    var ps = Array.apply(null, Array(120)).map(function () {
      return { x: Math.random() * cv.width, y: -10 - Math.random() * 120, r: 3 + Math.random() * 5, d: 2 + Math.random() * 3, c: colors[Math.floor(Math.random() * colors.length)] };
    });
    var f = 0;
    (function draw() {
      ctx.clearRect(0, 0, cv.width, cv.height);
      ps.forEach(function (p) { p.y += p.d; p.x += Math.sin((f + p.r * 10) / 20); ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, 6.2832); ctx.fillStyle = p.c; ctx.fill(); });
      f++;
      if (f < 200) requestAnimationFrame(draw); else { ctx.clearRect(0, 0, cv.width, cv.height); cv.style.display = 'none'; }
    })();
  }
})();
