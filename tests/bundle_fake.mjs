// Builds the sign-in code against in-memory fakes (never the real Firebase) so tests/e2e.py can run offline.
import { build } from 'esbuild';
const f = (n) => new URL(`./fakes/${n}.js`, import.meta.url).pathname;
await build({
  entryPoints: ['src/auth/index.js'], bundle: true, format: 'iife', outfile: '.build/js/auth.js',
  alias: { 'firebase/app': f('app'), 'firebase/auth': f('auth'), 'firebase/firestore': f('firestore'), 'firebase/app-check': f('app-check') },
  define: { __FIREBASE_CONFIG__: JSON.stringify({ apiKey: 'x', authDomain: 'demo.firebaseapp.com', projectId: 'demo', appId: 'x', appCheckSiteKey: '' }) },
});
