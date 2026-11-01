/* Techbase blog: a small, safe Markdown renderer used by the admin preview and by posts written in the admin area.
   It builds DOM nodes (never HTML strings), so nothing a writer types can run as script.
   Supported: ## headings, **bold**, *italic*, `code`, [links](url), - lists, 1. lists, > quotes, --- rules,
   ![description](photo:name) for site photos and ![description](img:id) for pictures uploaded in the admin area. */
(function () {
  'use strict';
  var TB = window.TB = window.TB || {};
  var rawBase = document.body.getAttribute('data-root') || '';
  var BASE = /^(?:(?:\.\.\/)*|\/)$/.test(rawBase) ? rawBase : '';
  var SAFE_URL = /^(?:https?:\/\/|mailto:|tel:|\/|\.{1,2}\/|#|[a-z0-9_-]+\/)/i;
  var NAME = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

  function el(tag, attrs, kids) {
    var n = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) { if (attrs[k] != null && attrs[k] !== false) n.setAttribute(k, attrs[k] === true ? '' : attrs[k]); });
    (kids || []).forEach(function (c) { n.appendChild(typeof c === 'string' ? document.createTextNode(c) : c); });
    return n;
  }
  function safeUrl(u) { return SAFE_URL.test(u) ? u : '#'; }

  /* A picture: site photo (photo:name) or uploaded picture (img:id). Anything else is dropped. */
  function picture(alt, src, ctx) {
    var m = /^(photo|img):([a-z0-9-]+)$/.exec(src);
    if (!m || !NAME.test(m[2])) return null;
    var img = el('img', { alt: alt || '', loading: 'lazy', decoding: 'async' });
    if (m[1] === 'photo') {
      var p = ctx && ctx.photos && ctx.photos[m[2]];
      if (!p) return null;
      var set = p.widths.map(function (w) { return BASE + 'assets/img/photos/' + m[2] + '-' + w + '.webp ' + w + 'w'; }).join(', ');
      img.src = BASE + 'assets/img/photos/' + m[2] + '-' + p['default'] + '.webp';
      img.setAttribute('srcset', set); img.setAttribute('sizes', '(min-width: 900px) 760px, 94vw');
      img.setAttribute('width', p.w); img.setAttribute('height', p.h);
      if (!alt) img.alt = p.alt || '';
    } else if (TB.live) {
      TB.live.image(m[2]).then(function (r) { if (r && r.data) img.src = r.data; if (r && !alt) img.alt = r.alt || ''; }, function () {});
    }
    return img;
  }

  var INLINE = '!\\[([^\\]]*)\\]\\(([^)\\s]+)\\)|\\[([^\\]]+)\\]\\(([^)\\s]+)\\)|\\*\\*(.+?)\\*\\*|\\*(?!\\s)(.+?)\\*|`([^`]+)`';
  function inline(text, parent, ctx) {
    var re = new RegExp(INLINE, 'g'), last = 0, m;
    while ((m = re.exec(text))) {
      if (m.index > last) parent.appendChild(document.createTextNode(text.slice(last, m.index)));
      if (m[2] !== undefined) { var im = picture(m[1], m[2], ctx); if (im) parent.appendChild(im); }
      else if (m[4] !== undefined) {
        var href = safeUrl(m[4]), ext = /^https?:/i.test(href);
        var a = el('a', { href: href, rel: ext ? 'noopener noreferrer' : null, target: ext ? '_blank' : null });
        inline(m[3], a, ctx); parent.appendChild(a);
      }
      else if (m[5] !== undefined) { var b = el('strong'); inline(m[5], b, ctx); parent.appendChild(b); }
      else if (m[6] !== undefined) { var i = el('em'); inline(m[6], i, ctx); parent.appendChild(i); }
      else parent.appendChild(el('code', {}, [m[7]]));
      last = re.lastIndex;
    }
    if (last < text.length) parent.appendChild(document.createTextNode(text.slice(last)));
  }

  var START = /^(?:#{1,4}\s|>\s?|\s*[-*]\s+|\s*\d+[.)]\s+|-{3,}\s*$|\*{3,}\s*$)/;
  function render(src, ctx) {
    var frag = document.createDocumentFragment();
    var lines = String(src || '').replace(/\r\n?/g, '\n').split('\n'), i = 0, m;
    while (i < lines.length) {
      var line = lines[i];
      if (!line.trim()) { i++; continue; }
      if ((m = /^(#{1,4})\s+(.*)$/.exec(line))) {
        var h = el('h' + Math.max(2, m[1].length)); inline(m[2].trim(), h, ctx); frag.appendChild(h); i++; continue;
      }
      if (/^(?:-{3,}|\*{3,})\s*$/.test(line)) { frag.appendChild(el('hr')); i++; continue; }
      if (/^>\s?/.test(line)) {
        var q = [];
        while (i < lines.length && /^>\s?/.test(lines[i])) { q.push(lines[i].replace(/^>\s?/, '')); i++; }
        var bq = el('blockquote'), bp = el('p'); inline(q.join(' ').trim(), bp, ctx); bq.appendChild(bp); frag.appendChild(bq); continue;
      }
      var ul = /^\s*[-*]\s+/, ol = /^\s*\d+[.)]\s+/;
      if (ul.test(line) || ol.test(line)) {
        var re = ul.test(line) ? ul : ol, list = el(re === ul ? 'ul' : 'ol');
        while (i < lines.length && re.test(lines[i])) { var li = el('li'); inline(lines[i].replace(re, '').trim(), li, ctx); list.appendChild(li); i++; }
        frag.appendChild(list); continue;
      }
      var para = [];
      while (i < lines.length && lines[i].trim() && (para.length === 0 || !START.test(lines[i]))) { para.push(lines[i].trim()); i++; }
      var text = para.join(' '), only = /^!\[([^\]]*)\]\(([^)\s]+)\)$/.exec(text);
      if (only) { var pic = picture(only[1], only[2], ctx); if (pic) frag.appendChild(el('figure', { 'class': 'body-fig' }, [pic])); continue; }
      var p = el('p'); inline(text, p, ctx); frag.appendChild(p);
    }
    return frag;
  }
  TB.md = { render: render, words: function (s) { return (String(s || '').match(/\w+/g) || []).length; } };
})();
