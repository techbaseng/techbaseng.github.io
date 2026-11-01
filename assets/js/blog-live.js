/* Techbase blog: reads posts written in the admin area straight from Firestore over plain HTTPS (no sign-in needed),
   so a post is visible the moment it is published. A nightly rebuild also turns them into permanent static pages. */
(function () {
  'use strict';
  var TB = window.TB = window.TB || {};
  var body = document.body;
  var rawBase = body.getAttribute('data-root') || '';
  var BASE = /^(?:(?:\.\.\/)*|\/)$/.test(rawBase) ? rawBase : '';
  var PROJECT = body.getAttribute('data-fb-project') || '', KEY = body.getAttribute('data-fb-key') || '';
  var OK = /^[a-z0-9-]{4,40}$/.test(PROJECT) && /^[A-Za-z0-9_-]{10,80}$/.test(KEY);
  var SLUG = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
  var MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  var API = 'https://firestore.googleapis.com/v1/projects/' + PROJECT + '/databases/(default)/documents';
  var el = function (t, a, k) { return TB.h(t, a, k); };

  function val(f) {
    if (!f) return '';
    if ('stringValue' in f) return f.stringValue;
    if ('booleanValue' in f) return f.booleanValue;
    if ('integerValue' in f) return +f.integerValue;
    if ('timestampValue' in f) return f.timestampValue;
    return '';
  }
  function decode(d) {
    var o = {}, F = d.fields || {};
    Object.keys(F).forEach(function (k) { o[k] = val(F[k]); });
    o.slug = String(d.name || '').split('/').pop();
    return o;
  }
  function dateLabel(iso) { var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso || ''); return m ? (+m[3]) + ' ' + MONTHS[+m[2] - 1] + ' ' + m[1] : ''; }

  var imgCache = {}, metaP = null;
  var live = TB.live = {
    ok: OK,
    dateLabel: dateLabel,
    list: function () {
      if (!OK) return Promise.resolve([]);
      var fields = ['title', 'summary', 'date', 'published', 'coverPhoto', 'coverImage', 'coverAlt', 'thumb'].map(function (f) { return { fieldPath: f }; });
      var q = { structuredQuery: { from: [{ collectionId: 'posts' }], select: { fields: fields }, where: { fieldFilter: { field: { fieldPath: 'published' }, op: 'EQUAL', value: { booleanValue: true } } } } };
      return fetch(API + ':runQuery?key=' + KEY, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(q) })
        .then(function (r) { return r.ok ? r.json() : []; })
        .then(function (rows) { return rows.filter(function (r) { return r.document; }).map(function (r) { return decode(r.document); }).filter(function (p) { return p.published === true && SLUG.test(p.slug); }).sort(function (a, b) { return a.date < b.date ? 1 : -1; }); })
        .catch(function () { return []; });
    },
    get: function (slug) {
      if (!OK || !SLUG.test(slug)) return Promise.resolve(null);
      return fetch(API + '/posts/' + slug + '?key=' + KEY).then(function (r) { return r.ok ? r.json() : null; })
        .then(function (d) { var p = d && decode(d); return p && p.published === true ? p : null; }).catch(function () { return null; });
    },
    image: function (id) {
      if (!SLUG.test(id)) return Promise.resolve(null);
      if (!imgCache[id]) {
        imgCache[id] = !OK ? Promise.resolve(null) : fetch(API + '/postImages/' + id + '?key=' + KEY).then(function (r) { return r.ok ? r.json() : null; })
          .then(function (d) { var o = d && decode(d); return o && /^data:image\//.test(o.data) ? o : null; }).catch(function () { return null; });
      }
      return imgCache[id];
    },
    remember: function (id, data, alt) { imgCache[id] = Promise.resolve({ data: data, alt: alt || '' }); },
    meta: function () {
      if (!metaP) metaP = fetch(BASE + 'assets/data/blog.json').then(function (r) { return r.json(); }).catch(function () { return { 'static': [], photos: {} }; });
      return metaP;
    },
  };

  function cover(p, photos) {
    if (p.thumb && /^data:image\//.test(p.thumb)) return el('img', { src: p.thumb, alt: p.coverAlt || '', loading: 'lazy', decoding: 'async' });
    var ph = p.coverPhoto && photos[p.coverPhoto];
    if (ph) return el('img', { src: BASE + 'assets/img/photos/' + p.coverPhoto + '-' + (ph.widths.indexOf(480) >= 0 ? 480 : ph['default']) + '.webp', alt: p.coverAlt || ph.alt || '', width: ph.w, height: ph.h, loading: 'lazy', decoding: 'async' });
    return el('div', { 'class': 'cover-fallback', 'aria-hidden': 'true' }, []);
  }

  /* ---- blog index: add posts that were published after the last site build ---- */
  var grid = document.querySelector('[data-live-list]');
  if (grid && OK) {
    Promise.all([live.list(), live.meta()]).then(function (r) {
      var have = {};
      Array.prototype.forEach.call(document.querySelectorAll('[data-slug]'), function (n) { have[n.getAttribute('data-slug')] = 1; });
      (r[1]['static'] || []).forEach(function (s) { have[s] = 1; });
      var fresh = r[0].filter(function (p) { return !have[p.slug]; });
      fresh.slice().reverse().forEach(function (p) {
        var a = el('a', { 'class': 'pcard', 'data-slug': p.slug, href: BASE + 'blog/post/index.html?s=' + p.slug }, [
          el('div', { 'class': 'pcard-img' }, [cover(p, r[1].photos || {})]),
          el('div', { 'class': 'pcard-body' }, [el('p', { 'class': 'pcard-meta' }, [dateLabel(p.date)]), el('h2', {}, [p.title]), el('p', {}, [p.summary])])]);
        grid.insertBefore(a, grid.firstChild);
      });
    });
  }

  /* ---- a single post that has no static page yet: blog/post/?s=slug ---- */
  var page = document.querySelector('[data-live-post]');
  if (page) {
    var slug = new URLSearchParams(location.search).get('s') || '';
    var $ = function (s) { return page.querySelector(s); };
    var state = $('[data-lp-state]'), article = $('[data-lp-article]');
    var fail = function (msg) { state.textContent = msg; state.hidden = false; };
    if (!SLUG.test(slug)) fail('That article address is not valid.');
    else Promise.all([live.get(slug), live.meta()]).then(function (r) {
      var p = r[0], meta = r[1];
      if ((meta['static'] || []).indexOf(slug) >= 0) { location.replace(BASE + 'blog/' + slug + '/index.html'); return; }
      if (!p) { fail('We could not find that article. It may have been moved or unpublished.'); return; }
      document.title = p.title + ' | Techbase';
      $('[data-lp-title]').textContent = p.title;
      $('[data-lp-date]').textContent = dateLabel(p.date); $('[data-lp-date]').setAttribute('datetime', p.date);
      $('[data-lp-read]').textContent = Math.max(1, Math.ceil(TB.md.words(p.body) / 200)) + ' min read';
      var cv = $('[data-lp-cover]'), done = function (src, alt, w, h) { if (!src) return; cv.appendChild(el('img', { src: src, alt: alt || '', width: w, height: h })); cv.hidden = false; };
      var ph = p.coverPhoto && meta.photos && meta.photos[p.coverPhoto];
      if (ph) done(BASE + 'assets/img/photos/' + p.coverPhoto + '-' + ph['default'] + '.webp', p.coverAlt || ph.alt, ph.w, ph.h);
      else if (p.coverImage) live.image(p.coverImage).then(function (im) { if (im) done(im.data, p.coverAlt || im.alt); });
      var bodyEl = $('[data-lp-body]');
      bodyEl.insertBefore(TB.md.render(p.body, { photos: meta.photos || {} }), bodyEl.firstChild);
      state.hidden = true; article.hidden = false;
      var link = $('[data-copy-link]'); if (link) link.setAttribute('data-copy-link', location.href);
      var wa = $('[data-lp-wa]'); if (wa) wa.href = 'https://wa.me/?text=' + encodeURIComponent(p.title + ' ' + location.href);
    });
  }
})();
