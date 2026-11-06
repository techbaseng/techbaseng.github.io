/* Techbase company pages: spotlight hover, path finder, testimonial slider, counters, filters,
   photo viewer, FAQ filter, forms, reading progress. Plain JavaScript, no dependencies. */
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* spotlight that follows the pointer */
  $$('.spot').forEach(function (el) {
    el.addEventListener('pointermove', function (e) {
      var r = el.getBoundingClientRect();
      el.style.setProperty('--mx', (e.clientX - r.left) + 'px');
      el.style.setProperty('--my', (e.clientY - r.top) + 'px');
    });
  });

  /* animated counters */
  var counters = $$('[data-count]');
  if (counters.length && 'IntersectionObserver' in window && !reduce) {
    var cio = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        cio.unobserve(en.target);
        var el = en.target, end = parseInt(el.getAttribute('data-count'), 10), t0 = null;
        var step = function (t) {
          if (t0 === null) t0 = t;
          var p = Math.min(1, (t - t0) / 1100);
          el.textContent = Math.round(end * (1 - Math.pow(1 - p, 3)));
          if (p < 1) requestAnimationFrame(step);
        };
        el.textContent = '0'; requestAnimationFrame(step);
      });
    }, { threshold: 0.5 });
    counters.forEach(function (c) { cio.observe(c); });
  }

  /* path finder tabs (arrow keys, roving tabindex) */
  $$('[data-pathfinder]').forEach(function (box) {
    var tabs = $$('[role="tab"]', box), panels = $$('[role="tabpanel"]', box);
    var select = function (i, focus) {
      tabs.forEach(function (t, j) { t.setAttribute('aria-selected', j === i ? 'true' : 'false'); t.tabIndex = j === i ? 0 : -1; });
      panels.forEach(function (p, j) { if (j === i) p.removeAttribute('data-js-hidden'); else p.setAttribute('data-js-hidden', ''); });
      if (focus) tabs[i].focus();
    };
    tabs.forEach(function (t, i) {
      t.addEventListener('click', function () { select(i); });
      t.addEventListener('keydown', function (e) {
        var k = e.key, n = tabs.length;
        if (k === 'ArrowRight') { e.preventDefault(); select((i + 1) % n, true); }
        else if (k === 'ArrowLeft') { e.preventDefault(); select((i - 1 + n) % n, true); }
        else if (k === 'Home') { e.preventDefault(); select(0, true); }
        else if (k === 'End') { e.preventDefault(); select(n - 1, true); }
      });
    });
  });

  /* testimonial slider + read more */
  $$('[data-slider]').forEach(function (box) {
    var track = $('.tslider-track', box);
    $$('[data-slide]', box).forEach(function (b) {
      b.addEventListener('click', function () {
        var card = track.querySelector('.tcard');
        var w = card ? card.getBoundingClientRect().width + 20 : 320;
        track.scrollBy({ left: w * parseInt(b.getAttribute('data-slide'), 10), behavior: reduce ? 'auto' : 'smooth' });
      });
    });
    track.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight') track.scrollBy({ left: 300 }); else if (e.key === 'ArrowLeft') track.scrollBy({ left: -300 });
    });
  });
  $$('[data-clamp]').forEach(function (p) {
    var btn = p.parentNode.parentNode.querySelector('[data-clamp-toggle]');
    if (!btn) return;
    p.classList.add('is-clamped');
    if (p.scrollHeight <= p.clientHeight + 2) { p.classList.remove('is-clamped'); return; }
    btn.hidden = false;
    btn.addEventListener('click', function () {
      var open = p.classList.toggle('is-clamped') === false;
      btn.textContent = open ? 'Show less' : 'Read more';
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  });

  /* portfolio year filter */
  $$('[data-filter-group]').forEach(function (g) {
    var items = $$('[data-year]', g.parentNode);
    $$('[data-filter]', g).forEach(function (b) {
      b.addEventListener('click', function () {
        var y = b.getAttribute('data-filter');
        $$('[data-filter]', g).forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
        items.forEach(function (it) { it.hidden = !(y === 'all' || it.getAttribute('data-year') === y); });
      });
    });
  });

  /* FAQ filter + open the question named in the address */
  var ff = $('#faq-filter');
  if (ff) {
    var qs = $$('.faq'), empty = $('#faq-empty');
    ff.addEventListener('input', function () {
      var q = ff.value.trim().toLowerCase(), n = 0;
      qs.forEach(function (d) { var ok = !q || d.getAttribute('data-search').indexOf(q) > -1; d.hidden = !ok; if (ok) n++; });
      if (empty) empty.classList.toggle('is-visible', n === 0);
    });
    var openHash = function () { var d = location.hash && $(location.hash); if (d && d.classList && d.classList.contains('faq')) d.open = true; };
    openHash(); window.addEventListener('hashchange', openHash);
  }

  /* photo viewer */
  var lb = $('#lightbox');
  if (lb && typeof lb.showModal === 'function') {
    var img = $('img', lb), cap = $('figcaption', lb);
    $$('[data-lightbox]').forEach(function (a) {
      a.addEventListener('click', function (e) {
        e.preventDefault();
        var thumb = $('img', a);
        img.src = a.getAttribute('href'); img.alt = thumb ? thumb.alt : '';
        cap.textContent = a.getAttribute('data-caption') || '';
        lb.showModal();
      });
    });
    lb.addEventListener('click', function (e) { if (e.target === lb || e.target.closest('.lb-close')) lb.close(); });
  }

  /* reading progress + copy link */
  var bar = $('#read-bar'), body = $('#article-body');
  if (bar && body) {
    var upd = function () {
      var r = body.getBoundingClientRect(), h = r.height - window.innerHeight * 0.6;
      bar.style.width = Math.max(0, Math.min(100, (-r.top + 80) / Math.max(h, 1) * 100)) + '%';
    };
    window.addEventListener('scroll', upd, { passive: true }); upd();
  }
  $$('[data-copy-link]').forEach(function (b) {
    b.addEventListener('click', function () {
      var url = b.getAttribute('data-copy-link');
      var done = function () { var l = $('[data-label]', b); if (l) l.textContent = 'Link copied'; if (window.TB) TB.toast('Link copied'); };
      if (navigator.clipboard) navigator.clipboard.writeText(url).then(done, function () { window.prompt('Copy this link', url); });
      else window.prompt('Copy this link', url);
    });
  });

  /* enquiry + application forms: stored in Firestore (create-only), see firebase/firestore.rules */
  var EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  $$('form[data-form]').forEach(function (form) {
    var status = $('[data-status]', form), btn = $('button[type="submit"]', form), label = $('[data-label]', btn);
    var say = function (msg, kind) { status.textContent = msg; status.className = 'form-status' + (kind ? ' is-' + kind : ''); };
    var fieldErr = function (name, msg) {
      var f = $('[data-field="' + name + '"]', form); if (!f) return;
      f.classList.toggle('has-error', !!msg); $('.err', f).textContent = msg || '';
      var inp = $('input,select,textarea', f); if (inp) inp.setAttribute('aria-invalid', msg ? 'true' : 'false');
    };
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var data = {}, bad = null;
      $$('input,select,textarea', form).forEach(function (el) { if (el.name) data[el.name] = (el.value || '').trim(); });
      if (data.website) return; // honeypot: real people leave this empty
      $$('[data-field]', form).forEach(function (f) {
        var el = $('input,select,textarea', f), n = el.name, msg = '';
        if (el.required && !data[n]) msg = 'This field is required.';
        else if (n === 'email' && data[n] && !EMAIL.test(data[n])) msg = 'Enter a valid email address.';
        else if (el.type === 'url' && data[n] && !/^https?:\/\/\S+\.\S+/.test(data[n])) msg = 'Enter a full link starting with https://';
        fieldErr(n, msg); if (msg && !bad) bad = el;
      });
      if (bad) { bad.focus(); say('Please fix the highlighted fields.', 'err'); return; }
      delete data.website;
      if (document.body.getAttribute('data-accounts') !== 'on') { say('Sending is not switched on yet. Please email us or use WhatsApp.', 'err'); return; }
      var last = 0; try { last = parseInt(localStorage.getItem('tb:form-last') || '0', 10); } catch (x) { /* ignore */ }
      if (Date.now() - last < 15000) { say('Please wait a few seconds before sending again.', 'err'); return; }
      btn.disabled = true; label.textContent = 'Sending…'; say('');
      TB.loadAuth().then(function () {
        if (!TB.auth) throw new Error('unavailable');
        return TB.auth.submitForm(form.getAttribute('data-form'), data);
      }).then(function () {
        try { localStorage.setItem('tb:form-last', String(Date.now())); } catch (x) { /* ignore */ }
        form.reset(); say('Thank you. We have your message and will reply soon.', 'ok');
      }).catch(function () {
        say('That did not send. Please try again, or email us or use WhatsApp.', 'err');
      }).then(function () { btn.disabled = false; label.textContent = form.getAttribute('data-form') === 'applications' ? 'Send application' : 'Send enquiry'; });
    });
  });
})();
