// In-memory stand-in for firebase/auth, used only by tests/e2e.py. Users live in localStorage.__fb_users.
const U = () => JSON.parse(localStorage.getItem('__fb_users') || '{}');
const SU = (u) => localStorage.setItem('__fb_users', JSON.stringify(u));
let cur = null, cbs = [];
const sess = () => { try { return JSON.parse(localStorage.getItem('__fb_sess') || 'null'); } catch (e) { return null; } };
const mk = (r) => r && { uid: r.uid, email: r.email, displayName: r.name, emailVerified: !!r.verified, providerData: [{ providerId: r.provider || 'password' }],
  reload: async () => {}, };
const emit = () => cbs.forEach((f) => f(cur));
const err = (code) => Object.assign(new Error(code), { code });
export const getAuth = () => ({ get currentUser() { return cur; } });
export const setPersistence = async () => {};
export const browserLocalPersistence = {};
export const onAuthStateChanged = (a, f) => { cbs.push(f); const s = sess(); cur = s ? mk(U()[s]) : null; setTimeout(() => f(cur), 20); };
export const createUserWithEmailAndPassword = async (a, email, pw) => {
  const us = U(); if (us[email]) throw err('auth/email-already-in-use');
  if (pw.length < 6) throw err('auth/weak-password');
  us[email] = { uid: 'u_' + email, email, pw, name: '' }; SU(us); localStorage.setItem('__fb_sess', JSON.stringify(email)); cur = mk(us[email]); emit(); return { user: cur };
};
export const signInWithEmailAndPassword = async (a, email, pw) => {
  const us = U(); if (!us[email] || us[email].pw !== pw) throw err('auth/invalid-credential');
  localStorage.setItem('__fb_sess', JSON.stringify(email)); cur = mk(us[email]); emit(); return { user: cur };
};
export class GoogleAuthProvider {}
export const signInWithPopup = async () => { const us = U(); us['g@x.com'] = { uid: 'u_g', email: 'g@x.com', name: 'Gina Google', provider: 'google.com', verified: true }; SU(us); localStorage.setItem('__fb_sess', '"g@x.com"'); cur = mk(us['g@x.com']); return { user: cur }; };
export const sendEmailVerification = async () => { localStorage.setItem('__fb_verif', String(+localStorage.getItem('__fb_verif') + 1)); };
export const sendPasswordResetEmail = async (a, e) => { localStorage.setItem('__fb_reset', e); };
export const signOut = async () => { localStorage.removeItem('__fb_sess'); cur = null; emit(); };
export const updateProfile = async (u, p) => { const us = U(); us[u.email].name = p.displayName; SU(us); cur = mk(us[u.email]); };
export const deleteUser = async (u) => { const us = U(); delete us[u.email]; SU(us); localStorage.removeItem('__fb_sess'); cur = null; };
export const reauthenticateWithCredential = async (u, c) => { if (U()[u.email].pw !== c.pw) throw err('auth/invalid-credential'); };
export const reauthenticateWithPopup = async () => {};
export const EmailAuthProvider = { credential: (email, pw) => ({ email, pw }) };
