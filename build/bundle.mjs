// Bundles the Firebase sign-in code into .build/js/auth.js. Runs in GitHub Actions before build.py.
// If the Firebase settings are not provided, nothing is bundled and the site builds with accounts switched off.
import { build } from 'esbuild';
import { rmSync, mkdirSync } from 'node:fs';

const env = process.env;
const cfg = {
  apiKey: (env.FIREBASE_API_KEY || '').trim(),
  authDomain: (env.FIREBASE_AUTH_DOMAIN || '').trim(),
  projectId: (env.FIREBASE_PROJECT_ID || '').trim(),
  appId: (env.FIREBASE_APP_ID || '').trim(),
  appCheckSiteKey: (env.FIREBASE_APPCHECK_SITE_KEY || '').trim(),
};
rmSync('.build/js', { recursive: true, force: true });
if (!cfg.apiKey || !cfg.authDomain || !cfg.projectId || !cfg.appId) {
  console.log('Firebase settings not provided: accounts will be switched off in this build.');
  process.exit(0);
}
mkdirSync('.build/js', { recursive: true });
await build({
  entryPoints: ['src/auth/index.js'],
  bundle: true,
  minify: true,
  format: 'iife',
  target: ['es2020'],
  outfile: '.build/js/auth.js',
  define: { __FIREBASE_CONFIG__: JSON.stringify(cfg) },
  legalComments: 'none',
});
console.log('Bundled sign-in code for project', cfg.projectId);
