/* Techbase admin: write, edit, publish and delete blog posts. Talks to TB.admin (built from src/auth/index.js);
   Firestore security rules decide who may really save, so this page is a convenience, not the lock. */
(function () {
  'use strict';
  var root = document.querySelector('[data-admin]');
  if (!root) return;
  var TB = window.TB, h = TB.h;
  var rawBase = document.body.getAttribute('data-root') || '';
  var BASE = /^(?:(?:\.\.\/)*|\/)$/.test(rawBase) ? rawBase : '';
  var $ = function (s, r) { return (r || root).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || root).querySelectorAll(s)); };
  var SLUG = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
  var loading = $('[data-auth-loading]'), notice = $('[data-notice]');
  if (!loading) return;
  var views = {};
  $$('[data-view]').forEach(function (v) { views[v.getAttribute('data-view')] = v; });
  function show(name) { Object.keys(views).forEach(function (k) { views[k].hidden = k !== name; }); loading.hidden = true; window.scrollTo(0, 0); }
  function say(msg, ok) { notice.hidden = !msg; notice.textContent = msg || ''; notice.classList.toggle('is-ok', !!ok); if (msg) notice.scrollIntoView({ block: 'nearest' }); }
  function slugify(t) { return String(t || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 70).replace(/-+$/, ''); }
  function today() { var d = new Date(), p = function (n) { return (n < 10 ? '0' : '') + n; }; return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()); }
  function randId() { return Math.random().toString(36).slice(2, 8) + Date.now().toString(36).slice(-4); }
  function ferr(name, msg) {
    var f = $('[data-field="' + name + '"]'); if (!f) return;
    f.classList.toggle('has-error', !!msg); var e = $('.err', f); if (e) e.textContent = msg || '';
    var i = $('input,textarea', f); if (i) i.setAttribute('aria-invalid', msg ? 'true' : 'false');
  }

  var meta = { 'static': [], photos: {} };
  var posts = [];
  var cur = null;          // the post being edited
  var isNew = true;

  TB.authReady.then(function (user) {
    if (!user) { show('signin'); return; }
    TB.admin.isAdmin().then(function (ok) {
      if (!ok) {
        $('[data-uid]').textContent = TB.admin.uid; $('[data-who]').textContent = user.email || user.displayName || '';
        show('denied'); return;
      }
      TB.live.meta().then(function (m) { meta = m; });
      loadList();
    });
  });

  /* ---------- access denied ---------- */
  $('[data-copy-uid]').addEventListener('click', function () {
    var b = this, l = $('[data-label]', b), uid = TB.admin.uid;
    var ok = function () { l.textContent = 'Copied'; setTimeout(function () { l.textContent = 'Copy account ID'; }, 1800); };
    if (navigator.clipboard) navigator.clipboard.writeText(uid).then(ok, function () {}); else { var t = $('[data-uid]'); var r = document.createRange(); r.selectNodeContents(t); getSelection().removeAllRanges(); getSelection().addRange(r); }
  });
  $('[data-signout]').addEventListener('click', function () { TB.auth.signOut().then(function () { location.reload(); }); });

  /* ---------- list ---------- */
  function loadList() {
    say('');
    TB.admin.listPosts().then(function (rows) {
      posts = rows.sort(function (a, b) { return a.date < b.date ? 1 : -1; });
      var ul = $('[data-post-list]'); while (ul.firstChild) ul.removeChild(ul.firstChild);
      $('[data-empty]').classList.toggle('is-visible', !posts.length);
      posts.forEach(function (p) {
        var li = h('li', {}, [
          h('div', { 'class': 'pr-main' }, [h('b', {}, [p.title]), h('small', {}, [TB.live.dateLabel(p.date) + ' · /' + p.slug + '/ '])]),
          h('span', { 'class': 'badge-state' + (p.published ? ' is-live' : '') }, [p.published ? 'Published' : 'Draft']),
          h('div', { 'class': 'pr-act' }, [h('button', { type: 'button', 'class': 'btn btn--sm btn--ghost', 'data-edit': p.slug }, ['Edit'])])]);
        ul.appendChild(li);
      });
      show('list');
    }, function (e) { show('list'); say(e.message); });
  }
  $('[data-new]').addEventListener('click', function () { openEditor(null); });
  $('[data-post-list]').addEventListener('click', function (e) {
    var b = e.target.closest('[data-edit]'); if (!b) return;
    var slug = b.getAttribute('data-edit');
    openEditor(posts.filter(function (p) { return p.slug === slug; })[0]);
  });

  /* ---------- editor ---------- */
  var f = { title: $('#ed-title'), slug: $('#ed-slug'), summary: $('#ed-summary'), date: $('#ed-date'), alt: $('#ed-coveralt'), body: $('#ed-body'), pub: $('#ed-published') };
  var form = views.editor, preview = $('[data-preview]'), coverBox = $('[data-cover-preview]');
  var slugTouched = false;

  function setCover(c) {            // c = { photo, image, data, alt } or null
    cur.coverPhoto = c ? (c.photo || '') : ''; cur.coverImage = c ? (c.image || '') : ''; cur.thumb = c ? (c.thumb || '') : '';
    while (coverBox.firstChild) coverBox.removeChild(coverBox.firstChild);
    var src = '';
    if (c && c.photo && meta.photos[c.photo]) src = BASE + 'assets/img/photos/' + c.photo + '-480.webp';
    else if (c && c.data) src = c.data;
    else if (c && c.thumb) src = c.thumb;
    coverBox.appendChild(src ? h('img', { src: src, alt: '' }) : h('span', {}, ['No cover photo yet']));
    $('[data-remove-cover]').hidden = !src;
    if (c && c.photo && !f.alt.value && meta.photos[c.photo]) f.alt.value = meta.photos[c.photo].alt || '';
  }

  function openEditor(p) {
    isNew = !p; cur = p ? JSON.parse(JSON.stringify(p)) : { coverPhoto: '', coverImage: '', thumb: '' };
    ['title', 'slug', 'summary', 'date', 'body'].forEach(function (k) { ferr(k, ''); });
    $('[data-editor-title]').textContent = p ? 'Edit post' : 'New post';
    f.title.value = p ? p.title : ''; f.slug.value = p ? p.slug : ''; f.slug.readOnly = !!p; slugTouched = !!p;
    f.summary.value = p ? p.summary : ''; f.date.value = p ? p.date : today(); f.body.value = p ? p.body : '';
    f.alt.value = p ? (p.coverAlt || '') : ''; f.pub.checked = p ? p.published === true : false;
    setCover(p && (p.coverPhoto || p.coverImage || p.thumb) ? { photo: p.coverPhoto, image: p.coverImage, thumb: p.thumb } : null);
    if (p && p.coverImage && !p.thumb) TB.live.image(p.coverImage).then(function (im) { if (im) setCover({ image: p.coverImage, data: im.data, thumb: p.thumb }); });
    $('[data-delete]').hidden = !p;
    var lv = $('[data-view-live]'); lv.hidden = !(p && p.published); if (p) lv.href = BASE + 'blog/post/index.html?s=' + p.slug;
    count(); draw(); show('editor'); f.title.focus();
  }
  function count() { $('[data-count]').textContent = f.summary.value.length + '/300'; }
  var drawT;
  function draw() {
    clearTimeout(drawT);
    drawT = setTimeout(function () {
      while (preview.firstChild) preview.removeChild(preview.firstChild);
      if (!f.body.value.trim()) { preview.appendChild(h('p', { 'class': 'hint' }, ['Your article appears here as you type.'])); return; }
      preview.appendChild(TB.md.render(f.body.value, { photos: meta.photos || {} }));
    }, 120);
  }
  f.body.addEventListener('input', draw);
  f.summary.addEventListener('input', count);
  f.title.addEventListener('input', function () { if (isNew && !slugTouched) f.slug.value = slugify(f.title.value); });
  f.slug.addEventListener('input', function () { slugTouched = true; });
  $('[data-cancel]').addEventListener('click', loadList);

  /* toolbar */
  function wrapSel(before, after, placeholder) {
    var t = f.body, s = t.selectionStart, e = t.selectionEnd, sel = t.value.slice(s, e) || placeholder;
    t.setRangeText(before + sel + after, s, e, 'select'); t.setSelectionRange(s + before.length, s + before.length + sel.length); t.focus(); draw();
  }
  function lines(prefixFn) {
    var t = f.body, s = t.selectionStart, e = t.selectionEnd, v = t.value;
    var a = v.lastIndexOf('\n', s - 1) + 1, b = v.indexOf('\n', e); if (b < 0) b = v.length;
    var block = v.slice(a, b) || 'Text', out = block.split('\n').map(prefixFn).join('\n');
    t.setRangeText(out, a, b, 'select'); t.focus(); draw();
  }
  function insertBlock(text) {
    var t = f.body, s = t.selectionEnd, v = t.value;
    var pre = s > 0 && v.charAt(s - 1) !== '\n' ? '\n\n' : (s > 0 && v.slice(s - 2, s) !== '\n\n' ? '\n' : '');
    var post = v.slice(s, s + 1) === '\n' ? '' : '\n\n';
    t.setRangeText(pre + text + post, s, s, 'end'); t.focus(); draw();
  }
  $('.md-tools').addEventListener('click', function (e) {
    var b = e.target.closest('[data-md]'); if (!b) return;
    switch (b.getAttribute('data-md')) {
      case 'h2': lines(function (l) { return '## ' + l.replace(/^#+\s*/, ''); }); break;
      case 'bold': wrapSel('**', '**', 'bold text'); break;
      case 'italic': wrapSel('*', '*', 'italic text'); break;
      case 'link': var u = window.prompt('Paste the address (https://… or /contact/ for a page on this site)', 'https://'); if (u) wrapSel('[', '](' + u.trim() + ')', 'link text'); break;
      case 'ul': lines(function (l) { return '- ' + l.replace(/^\s*[-*]\s+/, ''); }); break;
      case 'ol': var n = 0; lines(function (l) { n++; return n + '. ' + l.replace(/^\s*\d+[.)]\s+/, ''); }); break;
      case 'quote': lines(function (l) { return '> ' + l.replace(/^>\s?/, ''); }); break;
      case 'photo': openLibrary(function (name) { insertBlock('![' + ((meta.photos[name] || {}).alt || 'Photo') + '](photo:' + name + ')'); }); break;
      case 'upload': openUpload(function (r) { insertBlock('![' + r.alt + '](img:' + r.id + ')'); }); break;
    }
  });

  /* photo library */
  var lib = $('#lib-dialog'), libCb = null;
  function openLibrary(cb) {
    libCb = cb; var grid = $('[data-lib-grid]'); while (grid.firstChild) grid.removeChild(grid.firstChild);
    Object.keys(meta.photos || {}).forEach(function (name) {
      var p = meta.photos[name];
      grid.appendChild(h('button', { type: 'button', 'data-name': name }, [h('img', { src: BASE + 'assets/img/photos/' + name + '-480.webp', alt: '', loading: 'lazy', width: 160, height: 120 }), h('span', {}, [p.alt])]));
    });
    if (!grid.firstChild) grid.appendChild(h('p', { 'class': 'hint' }, ['The photo list could not be loaded. Refresh the page and try again.']));
    lib.showModal();
  }
  $('[data-lib-grid]').addEventListener('click', function (e) { var b = e.target.closest('[data-name]'); if (!b) return; lib.close(); if (libCb) libCb(b.getAttribute('data-name')); });
  $('[data-lib-cancel]').addEventListener('click', function () { lib.close(); });
  $('[data-pick-cover]').addEventListener('click', function () { openLibrary(function (name) { setCover({ photo: name }); }); });
  $('[data-remove-cover]').addEventListener('click', function () { setCover(null); f.alt.value = ''; });
  $('[data-upload-cover]').addEventListener('click', function () {
    openUpload(function (r) { f.alt.value = r.alt; setCover({ image: r.id, data: r.data, thumb: r.thumb }); }, true);
  });

  /* upload: shrink in the browser, save to Firestore, hand back the id */
  var up = $('#up-dialog'), upForm = $('[data-up-form]'), upFile = $('#up-file'), upAlt = $('#up-alt'), upCb = null, upCover = false, upImg = null;
  function readFile(file) {
    return new Promise(function (res, rej) { var r = new FileReader(); r.onload = function () { res(r.result); }; r.onerror = function () { rej(new Error('That file could not be read.')); }; r.readAsDataURL(file); });
  }
  function shrink(dataUrl, maxW, limit) {
    return new Promise(function (res, rej) {
      var im = new Image();
      im.onload = function () {
        var w = maxW, q = 0.82, out = '';
        for (var i = 0; i < 8; i++) {
          var s = Math.min(1, w / im.width), c = document.createElement('canvas');
          c.width = Math.max(1, Math.round(im.width * s)); c.height = Math.max(1, Math.round(im.height * s));
          c.getContext('2d').drawImage(im, 0, 0, c.width, c.height);
          out = c.toDataURL('image/jpeg', q);
          if (out.length <= limit) return res(out);
          q = Math.max(0.5, q - 0.08); w = Math.round(w * 0.85);
        }
        rej(new Error('That photo is too large even after shrinking. Try a smaller one.'));
      };
      im.onerror = function () { rej(new Error('That file is not a picture we can read.')); };
      im.src = dataUrl;
    });
  }
  function openUpload(cb, asCover) {
    upCb = cb; upCover = !!asCover; upImg = null; upFile.value = ''; upAlt.value = ''; ferr('file', ''); ferr('alt', '');
    var pv = $('[data-up-preview]'); while (pv.firstChild) pv.removeChild(pv.firstChild); pv.hidden = true;
    up.showModal();
  }
  upFile.addEventListener('change', function () {
    ferr('file', ''); upImg = null;
    var file = upFile.files[0]; if (!file) return;
    if (!/^image\/(jpeg|png|webp)$/.test(file.type)) { ferr('file', 'Choose a JPEG, PNG or WebP photo.'); return; }
    if (file.size > 25 * 1024 * 1024) { ferr('file', 'That file is very large. Choose one under 25 MB.'); return; }
    readFile(file).then(function (d) { return shrink(d, 1400, 380000); }).then(function (full) {
      upImg = { full: full }; var pv = $('[data-up-preview]'); while (pv.firstChild) pv.removeChild(pv.firstChild); pv.appendChild(h('img', { src: full, alt: 'Preview of the chosen photo' })); pv.hidden = false;
    }).catch(function (e) { ferr('file', e.message); });
  });
  upForm.addEventListener('submit', function (e) {
    e.preventDefault();
    if (!upImg) { ferr('file', 'Choose a photo first.'); return; }
    if (!upAlt.value.trim()) { ferr('alt', 'Describe what the photo shows, in a few words.'); return; }
    ferr('alt', '');
    var btn = $('[data-up-add]'); btn.disabled = true;
    var id = randId(), alt = upAlt.value.trim();
    var thumbP = upCover ? shrink(upImg.full, 640, 80000) : Promise.resolve('');
    thumbP.then(function (thumb) {
      return TB.admin.saveImage(id, upImg.full, alt).then(function () {
        TB.live.remember(id, upImg.full, alt); up.close(); if (upCb) upCb({ id: id, alt: alt, data: upImg.full, thumb: thumb });
      });
    }).catch(function (er) { ferr('file', er.message); }).then(function () { btn.disabled = false; });
  });
  $('[data-up-cancel]').addEventListener('click', function () { up.close(); });

  /* save */
  form.addEventListener('submit', function (e) {
    e.preventDefault(); say('');
    var title = f.title.value.trim(), slug = f.slug.value.trim(), summary = f.summary.value.trim(), body = f.body.value.trim(), date = f.date.value, bad = false;
    function need(name, cond, msg) { ferr(name, cond ? '' : msg); if (!cond) bad = true; }
    need('title', title.length > 0, 'Give the post a title.');
    need('slug', SLUG.test(slug) && slug.length >= 3, 'Use at least 3 letters, numbers or hyphens, for example my-first-post.');
    if (isNew && SLUG.test(slug)) need('slug', (meta['static'] || []).indexOf(slug) < 0 && !posts.some(function (p) { return p.slug === slug; }), 'There is already a post with this address. Change it a little.');
    need('summary', summary.length > 0, 'Write a short summary.');
    need('date', /^\d{4}-\d{2}-\d{2}$/.test(date), 'Choose a date.');
    need('body', body.length > 0, 'Write the article.');
    if (bad) { var first = $('.has-error input, .has-error textarea', form); if (first) first.focus(); return; }
    var btn = $('button[type=submit]', form), lab = $('[data-label]', btn); btn.disabled = true; lab.textContent = 'Saving…';
    var u = TB.auth.user;
    var post = { title: title, summary: summary, body: body, date: date, published: f.pub.checked, coverPhoto: cur.coverPhoto || '', coverImage: cur.coverImage || '', coverAlt: f.alt.value.trim(), thumb: cur.thumb || '', author: ((u && (u.displayName || '')) || '').slice(0, 80) };
    TB.admin.savePost(slug, post, isNew).then(function () {
      TB.toast(post.published ? 'Saved and published' : 'Saved as a draft');
      return loadListThen(function () { say(post.published ? 'Saved. The post is live on the blog now.' : 'Saved as a draft. Only administrators can see it.', true); });
    }).catch(function (er) { say(er.message); }).then(function () { btn.disabled = false; lab.textContent = 'Save post'; });
  });
  function loadListThen(fn) { return TB.admin.listPosts().then(function (rows) { posts = rows; loadList(); setTimeout(fn, 50); }); }

  /* delete */
  var del = $('#del-dialog');
  $('[data-delete]').addEventListener('click', function () { del.showModal(); });
  $('[data-del-cancel]').addEventListener('click', function () { del.close(); });
  $('[data-del-confirm]').addEventListener('click', function (e) {
    e.preventDefault(); del.close();
    var ids = [cur.coverImage].concat((cur.body.match(/\(img:([a-z0-9-]+)\)/g) || []).map(function (m) { return m.slice(5, -1); })).filter(Boolean);
    TB.admin.deletePost(cur.slug).then(function () {
      return Promise.all(ids.map(function (id) { return TB.admin.deleteImage(id).catch(function () {}); }));
    }).then(function () { TB.toast('Post deleted'); loadListThen(function () { say('The post was deleted.', true); }); }).catch(function (er) { say(er.message); });
  });
})();
