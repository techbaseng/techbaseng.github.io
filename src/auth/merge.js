// Progress snapshot helpers. A snapshot is plain JSON:
//   { done: { <course>: [lesson files] }, phases: { <localStorage key>: number }, last: { s, u, t, f, n, at } | null }
// Merging never loses work: done lists are unioned, phase counters take the larger value,
// and the most recently opened lesson wins.

export const PHASE_KEY = /^techbase_[a-z0-9-]+_l\d+$/i;

export function snapshotFromStorage(store) {
  const snap = { done: {}, phases: {}, last: null };
  for (let i = 0; i < store.length; i++) {
    const k = store.key(i);
    if (!k) continue;
    try {
      if (k.startsWith('tb:done:')) {
        const v = JSON.parse(store.getItem(k));
        if (Array.isArray(v) && v.length) snap.done[k.slice(8)] = v.filter((x) => typeof x === 'string');
      } else if (PHASE_KEY.test(k)) {
        const n = parseInt(store.getItem(k), 10);
        if (n > 1) snap.phases[k] = n;
      } else if (k === 'tb:last') {
        const v = JSON.parse(store.getItem(k));
        if (v && typeof v.u === 'string') snap.last = { s: v.s || '', u: v.u, t: String(v.t || ''), at: v.at || 0 };
      }
    } catch (e) { /* ignore unreadable keys */ }
  }
  return snap;
}

export function mergeSnapshots(a, b) {
  const out = { done: {}, phases: {}, last: null };
  const courses = new Set([...Object.keys(a?.done || {}), ...Object.keys(b?.done || {})]);
  for (const c of courses) out.done[c] = [...new Set([...(a?.done?.[c] || []), ...(b?.done?.[c] || [])])].sort();
  const keys = new Set([...Object.keys(a?.phases || {}), ...Object.keys(b?.phases || {})]);
  for (const k of keys) out.phases[k] = Math.max(a?.phases?.[k] || 0, b?.phases?.[k] || 0);
  const la = a?.last, lb = b?.last;
  out.last = la && lb ? ((lb.at || 0) > (la.at || 0) ? lb : la) : (la || lb || null);
  return out;
}

export function sameSnapshot(a, b) {
  return JSON.stringify(mergeSnapshots(a, a)) === JSON.stringify(mergeSnapshots(b, b));
}

export function applySnapshotToStorage(store, snap) {
  for (const [c, files] of Object.entries(snap.done || {})) {
    if (!/^[a-z0-9-]+$/.test(c)) continue;
    store.setItem('tb:done:' + c, JSON.stringify(files));
  }
  for (const [k, n] of Object.entries(snap.phases || {})) {
    if (PHASE_KEY.test(k) && Number.isInteger(n)) store.setItem(k, String(n));
  }
  if (snap.last) store.setItem('tb:last', JSON.stringify(snap.last));
}

// Keep what we send to the database small and well-formed (Firestore rules re-check this).
export function sanitise(snap) {
  const out = { done: {}, phases: {}, last: null };
  for (const [c, files] of Object.entries(snap.done || {})) {
    if (/^[a-z0-9-]{1,40}$/.test(c)) out.done[c] = files.filter((f) => /^[a-z0-9_.-]{1,40}$/i.test(f)).slice(0, 600);
  }
  for (const [k, n] of Object.entries(snap.phases || {})) {
    if (PHASE_KEY.test(k) && n > 0 && n < 1000) out.phases[k] = n;
  }
  if (snap.last && /^[a-z0-9-]+\/lessons\/[a-z0-9_.-]+$/i.test(snap.last.u)) {
    out.last = { s: String(snap.last.s || '').slice(0, 40), u: snap.last.u, t: String(snap.last.t || '').slice(0, 160), at: Number(snap.last.at) || 0 };
  }
  return out;
}
