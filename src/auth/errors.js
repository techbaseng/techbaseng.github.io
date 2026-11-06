// Turns Firebase error codes into short, kind sentences. Wording avoids revealing whether an email has an account.
const MESSAGES = {
  'permission-denied': 'This account is not allowed to do that. Check that it has been set up as an administrator (see FIREBASE_LOGIN_SETUP.md, Step 8).',
  'unavailable': 'No connection. Check your internet and try again.',
  'auth/invalid-email': 'That email address does not look right.',
  'auth/missing-password': 'Enter your password.',
  'auth/weak-password': 'Choose a password with at least 8 characters.',
  'auth/email-already-in-use': 'We could not create that account. If you already have one, try signing in or resetting your password.',
  'auth/invalid-credential': 'That email and password do not match. Check them and try again, or reset your password.',
  'auth/wrong-password': 'That email and password do not match. Check them and try again, or reset your password.',
  'auth/user-not-found': 'That email and password do not match. Check them and try again, or reset your password.',
  'auth/too-many-requests': 'Too many attempts. Please wait a few minutes and try again.',
  'auth/network-request-failed': 'No connection. Check your internet and try again.',
  'auth/popup-blocked': 'Your browser blocked the Google window. Allow pop-ups for this site and try again.',
  'auth/popup-closed-by-user': '',
  'auth/cancelled-popup-request': '',
  'auth/requires-recent-login': 'For your security, please sign in again and then repeat this.',
  'auth/user-disabled': 'This account has been disabled. Please contact us.',
  'auth/unauthorized-domain': 'This website address is not approved for sign-in yet. The site owner needs to add it in Firebase (see FIREBASE_LOGIN_SETUP.md).',
  'auth/operation-not-allowed': 'This sign-in method is not switched on yet. The site owner needs to enable it in Firebase.',
};
export function friendly(err) {
  const code = err && err.code;
  if (code && code in MESSAGES) return MESSAGES[code];
  return 'Something went wrong. Please try again.';
}
