import test from 'node:test';
import assert from 'node:assert/strict';
import { mergeSnapshots, sanitise, snapshotFromStorage, applySnapshotToStorage, sameSnapshot } from './merge.js';

class Store {
  constructor() { this.m = new Map(); }
  get length() { return this.m.size; }
  key(i) { return [...this.m.keys()][i] ?? null; }
  getItem(k) { return this.m.has(k) ? this.m.get(k) : null; }
  setItem(k, v) { this.m.set(k, String(v)); }
}

test('done lists are unioned and phases take the larger value', () => {
  const a = { done: { 'techbase-css': ['lesson_01.html'] }, phases: { techbase_css_l02: 3 }, last: { u: 'techbase-css/lessons/lesson_02.html', t: 'A', at: 5 } };
  const b = { done: { 'techbase-css': ['lesson_02.html'], 'techbase-html': ['lesson_01.html'] }, phases: { techbase_css_l02: 2, techbase_css_l03: 4 }, last: { u: 'techbase-html/lessons/lesson_01.html', t: 'B', at: 9 } };
  const m = mergeSnapshots(a, b);
  assert.deepEqual(m.done['techbase-css'], ['lesson_01.html', 'lesson_02.html']);
  assert.deepEqual(m.done['techbase-html'], ['lesson_01.html']);
  assert.equal(m.phases.techbase_css_l02, 3);
  assert.equal(m.phases.techbase_css_l03, 4);
  assert.equal(m.last.t, 'B');
});

test('merging with nothing changes nothing', () => {
  const a = { done: { x: ['a'] }, phases: {}, last: null };
  assert.ok(sameSnapshot(mergeSnapshots(a, null), a));
});

test('storage round trip', () => {
  const s = new Store();
  s.setItem('tb:done:techbase-css', JSON.stringify(['lesson_01.html']));
  s.setItem('techbase_css_l05', '4');
  s.setItem('tb:last', JSON.stringify({ s: 'techbase-css', u: 'techbase-css/lessons/lesson_01.html', t: 'T', at: 1 }));
  s.setItem('unrelated', 'x');
  const snap = snapshotFromStorage(s);
  assert.deepEqual(snap.done, { 'techbase-css': ['lesson_01.html'] });
  assert.equal(snap.phases.techbase_css_l05, 4);
  const t = new Store();
  applySnapshotToStorage(t, snap);
  assert.equal(t.getItem('techbase_css_l05'), '4');
  assert.equal(t.getItem('unrelated'), null);
});

test('sanitise drops malformed entries', () => {
  const out = sanitise({ done: { 'bad key!': ['a'], ok: ['x.html', '<script>'] }, phases: { evil: 5, techbase_css_l01: 2 }, last: { u: 'http://evil', t: 'x' } });
  assert.deepEqual(Object.keys(out.done), ['ok']);
  assert.deepEqual(out.done.ok, ['x.html']);
  assert.deepEqual(Object.keys(out.phases), ['techbase_css_l01']);
  assert.equal(out.last, null);
});
