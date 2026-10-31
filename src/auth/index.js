// Techbase sign-in, account and progress sync. Bundled by build/bundle.mjs and loaded on demand as assets/js/auth.js.
// Firebase settings are injected at build time from GitHub Actions secrets (see docs/FIREBASE_LOGIN_SETUP.md).
import { initializeApp } from 'firebase/app';
import {
  getAuth, onAuthStateChanged, createUserWithEmailAndPassword, signInWithEmailAndPassword, signInWithPopup,
  GoogleAuthProvider, sendEmailVerification, sendPasswordResetEmail, signOut, updateProfile, deleteUser,
  reauthenticateWithCredential, reauthenticateWithPopup, EmailAuthProvider, setPersistence, browserLocalPersistence,
} from 'firebase/auth';
import { getFirestore, doc, getDoc, setDoc, deleteDoc, collection, addDoc, serverTimestamp } from 'firebase/firestore';
import { initializeAppCheck, ReCaptchaV3Provider } from 'firebase/app-check';
import { snapshotFromStorage, mergeSnapshots, applySnapshotToStorage, sanitise, sameSnapshot } from './merge.js';
import { friendly } from './errors.js';

/* global __FIREBASE_CONFIG__ */
const cfg = __FIREBASE_CONFIG__;
const TB = window.TB;
const app = initializeApp({ apiKey: cfg.apiKey, authDomain: cfg.authDomain, projectId: cfg.projectId, appId: cfg.appId });
if (cfg.appCheckSiteKey) {
  try { initializeAppCheck(app, { provider: new ReCaptchaV3Provider(cfg.appCheckSiteKey), isTokenAutoRefreshEnabled: true }); } catch (e) { /* App Check is optional */ }
}
const auth = getAuth(app);
const db = getFirestore(app);
setPersistence(auth, browserLocalPersistence).catch(() => {});

let current = null;
let pushTimer = null;
let syncing = false;

const progressRef = (uid) => doc(db, 'progress', uid);
const userRef = (uid) => doc(db, 'users', uid);

async function pullAndMerge(user) {
  syncing = true;
  try {
    const local = snapshotFromStorage(localStorage);
    const remoteDoc = await getDoc(progressRef(user.uid));
    const remote = remoteDoc.exists() ? remoteDoc.data() : { done: {}, phases: {}, last: null };
    const merged = mergeSnapshots(local, remote);
    applySnapshotToStorage(localStorage, merged);
    window.dispatchEvent(new CustomEvent('tb:repaint'));
    if (!remoteDoc.exists() || !sameSnapshot(merged, remote)) {
      await setDoc(progressRef(user.uid), { ...sanitise(merged), updatedAt: serverTimestamp() });
    }
  } catch (e) { /* offline or rules not deployed yet: local progress keeps working */ }
  syncing = false;
}

function schedulePush() {
  if (!current || syncing) return;
  clearTimeout(pushTimer);
  pushTimer = setTimeout(async () => {
    try {
      const snap = sanitise(mergeSnapshots(snapshotFromStorage(localStorage), { done: {}, phases: {}, last: null }));
      await setDoc(progressRef(current.uid), { ...snap, updatedAt: serverTimestamp() });
    } catch (e) { /* will retry on next change */ }
  }, 1500);
}
document.addEventListener('tb:progress', schedulePush);
document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') { clearTimeout(pushTimer); pushTimer = null; if (current) schedulePush(); } });

async function ensureProfile(user, extra = {}) {
  try {
    const snap = await getDoc(userRef(user.uid));
    if (!snap.exists()) {
      await setDoc(userRef(user.uid), { name: (user.displayName || extra.name || '').slice(0, 80), goal: extra.goal || '', createdAt: serverTimestamp() });
    }
  } catch (e) { /* non-fatal */ }
}

let firstState = true;
onAuthStateChanged(auth, async (user) => {
  current = user;
  if (user) await pullAndMerge(user);
  TB.announceAuth(user || null);
  if (firstState) { firstState = false; }
});

// After a sign-in, bring progress across and tell the page before it navigates away.
async function settle(user) {
  current = user;
  await pullAndMerge(user);
  TB.announceAuth(user);
}

async function wrap(fn) {
  try { return await fn(); } catch (e) { const err = new Error(friendly(e)); err.code = e && e.code; throw err; }
}

TB.auth = {
  get user() { return auth.currentUser; },
  signIn: (email, password) => wrap(async () => { const c = await signInWithEmailAndPassword(auth, email, password); await settle(c.user); return c.user; }),
  async signUp({ name, email, password, goal }) {
    return wrap(async () => {
      const cred = await createUserWithEmailAndPassword(auth, email, password);
      await updateProfile(cred.user, { displayName: name });
      current = cred.user;
      await ensureProfile(cred.user, { name, goal });
      try { await sendEmailVerification(cred.user); } catch (e) { /* user can resend */ }
      TB.announceAuth(cred.user);
      return cred.user;
    });
  },
  async google() {
    return wrap(async () => {
      const cred = await signInWithPopup(auth, new GoogleAuthProvider());
      await ensureProfile(cred.user);
      await settle(cred.user);
      return cred.user;
    });
  },
  reset: (email) => wrap(() => sendPasswordResetEmail(auth, email)),
  signOut: () => wrap(async () => { await signOut(auth); }),
  resendVerification: () => wrap(() => sendEmailVerification(auth.currentUser)),
  async refresh() { return wrap(async () => { await auth.currentUser.reload(); TB.announceAuth(auth.currentUser); return auth.currentUser; }); },
  async saveProfile({ name, goal }) {
    return wrap(async () => {
      await updateProfile(auth.currentUser, { displayName: name });
      await setDoc(userRef(auth.currentUser.uid), { name: name.slice(0, 80), goal: goal || '' }, { merge: true });
      TB.announceAuth(auth.currentUser);
    });
  },
  async getProfile() { try { const s = await getDoc(userRef(auth.currentUser.uid)); return s.exists() ? s.data() : {}; } catch (e) { return {}; } },
  usesPassword() { return !!auth.currentUser && auth.currentUser.providerData.some((p) => p.providerId === 'password'); },
  async deleteAccount(password) {
    return wrap(async () => {
      const u = auth.currentUser;
      if (u.providerData.some((p) => p.providerId === 'password')) {
        await reauthenticateWithCredential(u, EmailAuthProvider.credential(u.email, password));
      } else {
        await reauthenticateWithPopup(u, new GoogleAuthProvider());
      }
      try { await deleteDoc(progressRef(u.uid)); await deleteDoc(userRef(u.uid)); } catch (e) { /* rules allow owner delete */ }
      await deleteUser(u);
    });
  },
  async submitForm(kind, data) {
    if (kind !== 'enquiries' && kind !== 'applications') throw new Error('bad form');
    await addDoc(collection(db, kind), { ...data, createdAt: serverTimestamp() });
  },
};
