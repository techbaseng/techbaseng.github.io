/* Sign-in, sign-up, reset and account page behaviour. Talks to window.TB.auth (assets/js/auth.js, built from src/auth). */
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var rawBase = document.body.getAttribute('data-root') || '';
  var BASE = /^(?:(?:\.\.\/)*|\/)$/.test(rawBase) ? rawBase : '';
  var EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  var loading = $('[data-auth-loading]'), ready = $('[data-auth-ready]');
  if (!loading && !ready) return;

  var notice = $('[data-notice]');
  function say(msg, ok) { if (!notice) return; notice.hidden = !msg; notice.textContent = msg || ''; notice.classList.toggle('is-ok', !!ok); if (msg) notice.scrollIntoView({ block: 'nearest' }); }
  function ferr(form, name, msg) {
    var f = $('[data-field="' + name + '"]', form); if (!f) return;
    f.classList.toggle('has-error', !!msg); var e = $('.err', f); if (e) e.textContent = msg || '';
    var i = $('input,select', f); if (i) i.setAttribute('aria-invalid', msg ? 'true' : 'false');
  }
  function busy(btn, on, text) { var l = $('[data-label]', btn); btn.disabled = on; if (l) { if (on) { btn.dataset.t = l.textContent; l.textContent = text || 'Please wait…'; } else if (btn.dataset.t) l.textContent = btn.dataset.t; } }
  function next() { var q = new URLSearchParams(location.search).get('next'); return q && /^[a-z0-9\/_.-]+$/i.test(q) && q.indexOf('..') < 0 ? BASE + q.replace(/^\//, '') : BASE + 'learn/index.html'; }
  function show() { if (loading) loading.hidden = true; if (ready) ready.hidden = false; }

  TB.authReady.then(function (user) {
    show();
    if ($('[data-auth-page]')) initLogin(user);
    if ($('[data-account-page]')) initAccount(user);
  });
  /* If the sign-in code could not load (offline, blocked), say so instead of spinning forever. */
  setTimeout(function () { if (loading && !loading.hidden && !TB.auth) { loading.hidden = true; var p = $('[data-auth-page],[data-account-page] .wrap'); if (p) p.insertBefore(TB.h('p', { 'class': 'auth-notice' }, ['Sign-in could not load. Check your connection and refresh the page.']), p.firstChild); } }, 12000);

  /* ---------------- login page ---------------- */
  function initLogin(user) {
    var panels = $$('[data-panel]'), tabs = $$('[data-tab]'), tabbar = $('[data-tabs]');
    var titles = { signin: ['Welcome back', 'Sign in to continue learning where you stopped.'], signup: ['Create your free account', 'Save your progress and unlock every lesson. No card needed.'], reset: ['Reset your password', 'Enter your email and we will send you a link.'], verify: ['Check your email', ''] };
    function go(name) {
      say('');
      panels.forEach(function (p) { p.hidden = p.getAttribute('data-panel') !== name; });
      tabs.forEach(function (t) { var on = t.getAttribute('data-tab') === name; t.setAttribute('aria-selected', on ? 'true' : 'false'); t.tabIndex = on ? 0 : -1; });
      if (tabbar) tabbar.hidden = name === 'reset' || name === 'verify';
      $('[data-title]').textContent = titles[name][0]; $('[data-sub]').textContent = titles[name][1];
      try { history.replaceState(null, '', name === 'signup' ? '#signup' : location.pathname + location.search); } catch (e) { /* ignore */ }
    }
    tabs.forEach(function (t) { t.addEventListener('click', function () { go(t.getAttribute('data-tab')); }); });
    $$('[data-go]').forEach(function (b) { b.addEventListener('click', function () { go(b.getAttribute('data-go')); }); });
    go(location.hash === '#signup' ? 'signup' : 'signin');
    if (user) { say('You are signed in. Taking you to the Academy…', true); setTimeout(function () { location.href = next(); }, 600); return; }

    $$('[data-pw-toggle]').forEach(function (b) {
      b.addEventListener('click', function () {
        var inp = b.parentNode.querySelector('input'), show = inp.type === 'password';
        inp.type = show ? 'text' : 'password'; b.setAttribute('aria-pressed', show ? 'true' : 'false'); b.setAttribute('aria-label', show ? 'Hide password' : 'Show password');
      });
    });
    var pwNew = $('#f-password-new'), meter = $('[data-meter]');
    if (pwNew && meter) pwNew.addEventListener('input', function () {
      var v = pwNew.value, s = 0; if (v.length >= 8) s++; if (v.length >= 12 || /\s/.test(v)) s++; if (/[A-Z]/.test(v) && /[0-9\W]/.test(v) && /[a-z]/.test(v)) s++;
      meter.style.width = v ? (s * 33 + (v.length ? 1 : 0)) + '%' : '0'; meter.setAttribute('data-level', String(Math.max(1, s)));
    });

    function done(u, verifyEmail) {
      if (verifyEmail) { go('verify'); $('[data-email]').textContent = u.email; $('[data-continue]').href = next(); }
      else location.href = next();
    }
    function formSubmit(name, handler) {
      var form = $('[data-auth-form="' + name + '"]'); if (!form) return;
      form.addEventListener('submit', function (e) {
        e.preventDefault(); say('');
        var btn = $('button[type="submit"]', form), d = {}, bad = null;
        $$('input,select', form).forEach(function (i) { d[i.name] = i.type === 'checkbox' ? i.checked : i.value.trim(); if (i.name === 'password') d.password = i.value; });
        $$('[data-field]', form).forEach(function (f) {
          var n = f.getAttribute('data-field'), msg = '';
          if (n === 'email') { if (!EMAIL.test(d.email || '')) msg = 'Enter a valid email address.'; }
          if (n === 'name' && !d.name) msg = 'Enter your name.';
          if (n === 'password') { if (!d.password) msg = 'Enter your password.'; else if (name === 'signup' && d.password.length < 8) msg = 'Use at least 8 characters.'; }
          if (n === 'agree' && !d.agree) msg = 'Please confirm you have read the privacy notice.';
          ferr(form, n, msg); if (msg && !bad) bad = $('input', f);
        });
        if (bad) { bad.focus(); return; }
        busy(btn, true);
        Promise.resolve(handler(d)).catch(function (err) { if (err && err.message) say(err.message); }).then(function () { busy(btn, false); });
      });
    }
    formSubmit('signin', function (d) { return TB.auth.signIn(d.email, d.password).then(function () { done(); }); });
    formSubmit('signup', function (d) { return TB.auth.signUp({ name: d.name, email: d.email, password: d.password, goal: d.goal }).then(function (u) { done(u, true); }); });
    formSubmit('reset', function (d) { return TB.auth.reset(d.email).then(function () { say('If an account exists for that email, a reset link is on its way. Check your spam folder too.', true); }); });
    $$('[data-google]').forEach(function (b) { b.addEventListener('click', function () { say(''); b.disabled = true; TB.auth.google().then(function () { done(); }).catch(function (err) { if (err && err.message) say(err.message); }).then(function () { b.disabled = false; }); }); });
    var resend = $('[data-resend]'); if (resend) resend.addEventListener('click', function () { resend.disabled = true; TB.auth.resendVerification().then(function () { say('Verification email sent again.', true); }).catch(function (e) { say(e.message); }).then(function () { setTimeout(function () { resend.disabled = false; }, 30000); }); });
  }

  /* ---------------- account page ---------------- */
  function initAccount(user) {
    if (!user) { location.replace(BASE + 'login/index.html?next=account/index.html'); return; }
    var nameEl = $('[data-name]'), emailEl = $('[data-email]'), av = $('[data-avatar]');
    function paintHead(u) {
      var nm = u.displayName || u.email.split('@')[0];
      nameEl.textContent = nm; emailEl.textContent = u.email; av.textContent = nm.charAt(0).toUpperCase();
      $('[data-verified]').hidden = !u.emailVerified; $('[data-verify-banner]').hidden = u.emailVerified;
      $('[name="name"]', $('[data-account-form="profile"]')).value = u.displayName || '';
    }
    paintHead(user); show();
    TB.auth.getProfile().then(function (p) { var g = $('[name="goal"]'); if (g && p.goal) g.value = p.goal; });
    $('[data-password-note]').textContent = TB.auth.usesPassword() ? 'We will email you a link to choose a new password.' : 'You sign in with Google, so there is no password to change here.';
    if (!TB.auth.usesPassword()) $('[data-reset-password]').hidden = true;

    var form = $('[data-account-form="profile"]');
    form.addEventListener('submit', function (e) {
      e.preventDefault(); say('');
      var name = form.elements.name.value.trim(); if (!name) { ferr(form, 'name', 'Enter your name.'); return; } ferr(form, 'name', '');
      var btn = $('button[type="submit"]', form); busy(btn, true, 'Saving…');
      TB.auth.saveProfile({ name: name, goal: form.elements.goal.value }).then(function () { paintHead(TB.auth.user); say('Saved.', true); }).catch(function (er) { say(er.message); }).then(function () { busy(btn, false); });
    });
    var rs = $('[data-resend]'); if (rs) rs.addEventListener('click', function () { TB.auth.resendVerification().then(function () { say('Verification email sent.', true); }).catch(function (er) { say(er.message); }); });
    var rf = $('[data-refresh]'); if (rf) rf.addEventListener('click', function () { TB.auth.refresh().then(function (u) { paintHead(u); say(u.emailVerified ? 'Email verified. Thank you.' : 'Not verified yet. Open the link in the email first.', u.emailVerified); }).catch(function (er) { say(er.message); }); });
    var rp = $('[data-reset-password]'); if (rp) rp.addEventListener('click', function () { TB.auth.reset(user.email).then(function () { say('Password reset email sent to ' + user.email + '.', true); }).catch(function (er) { say(er.message); }); });
    $('[data-signout]', $('.account-main')).addEventListener('click', function (e) { e.stopPropagation(); TB.auth.signOut().then(function () { location.href = BASE + 'index.html'; }); });

    function paintProgress() {
      $$('[data-progress-list] li').forEach(function (li) {
        var s = li.getAttribute('data-course'), n = parseInt(li.getAttribute('data-count'), 10), c = 0;
        try { c = (JSON.parse(localStorage.getItem('tb:done:' + s) || '[]') || []).length; } catch (e) { c = 0; }
        $('.bar > i', li).style.width = Math.min(100, Math.round(c / n * 100)) + '%';
        $('[data-text]', li).textContent = c ? c + ' of ' + n + ' done' : 'Not started';
      });
    }
    paintProgress(); window.addEventListener('tb:repaint', paintProgress);

    var dlg = $('#delete-dialog'), pwBox = $('[data-delete-password]');
    $('[data-delete-open]').addEventListener('click', function () { pwBox.hidden = !TB.auth.usesPassword(); $('#e-del-pw').textContent = ''; dlg.showModal(); });
    $('[data-delete-cancel]').addEventListener('click', function () { dlg.close(); });
    $('[data-delete-form]').addEventListener('submit', function (e) {
      e.preventDefault(); var btn = $('[data-delete-confirm]'), pw = $('#f-del-pw').value;
      if (TB.auth.usesPassword() && !pw) { $('#e-del-pw').textContent = 'Enter your password to confirm.'; return; }
      busy(btn, true, 'Deleting…');
      TB.auth.deleteAccount(pw).then(function () { TB.announceAuth(null); location.href = BASE + 'index.html'; })
        .catch(function (er) { $('#e-del-pw').textContent = er.message; busy(btn, false); });
    });
  }
})();
