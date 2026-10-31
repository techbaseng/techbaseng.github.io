"""Browser tests for accounts, gate, progress sync and forms, against a build made with tests/bundle_fake.mjs.
Run: node tests/bundle_fake.mjs && FIREBASE_*=x python3 build/build.py && python3 -m http.server -d dist 8123 & python3 tests/e2e.py"""
import json
import sys

from playwright.sync_api import sync_playwright

B = 'http://localhost:8123/'
fails = []
def check(name, cond):
    print(('PASS ' if cond else 'FAIL ') + name)
    if not cond: fails.append(name)
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={'width': 1280, 'height': 900}); pg = ctx.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    # signed out: free lesson open, second locked
    pg.goto(B + 'techbase-css/lessons/lesson_01.html'); pg.wait_for_timeout(400)
    check('first lesson not gated', pg.locator('#gate-wall').count() == 0)
    pg.goto(B + 'techbase-css/lessons/lesson_02.html'); pg.wait_for_timeout(400)
    check('second lesson gated when signed out', pg.locator('#gate-wall').count() == 1)
    pg.goto(B + 'techbase-css/index.html'); pg.wait_for_timeout(400)
    check('course page shows locks', pg.locator('.lesson.is-locked').count() > 50)
    # local progress made before signing up
    pg.goto(B + 'techbase-css/lessons/lesson_01.html'); pg.wait_for_timeout(300)
    pg.evaluate("localStorage.setItem('tb:done:techbase-scratch', JSON.stringify(['lesson_02.html']))")
    # sign up
    pg.goto(B + 'login/index.html#signup'); pg.wait_for_selector('[data-panel="signup"]:not([hidden])')
    pg.fill('#f-name', 'Ada Lovelace'); pg.fill('#f-email-up', 'ada@example.com'); pg.fill('#f-password-new', 'short')
    pg.check('#f-agree'); pg.click('[data-auth-form="signup"] button[type=submit]')
    check('weak password rejected client-side', 'at least 8' in pg.inner_text('#e-password-new').lower() or 'Use at least 8' in pg.inner_text('#e-password-new'))
    pg.fill('#f-password-new', 'correct horse battery'); pg.click('[data-auth-form="signup"] button[type=submit]')
    pg.wait_for_selector('#panel-verify:not([hidden])')
    check('verify panel shows email', 'ada@example.com' in pg.inner_text('#panel-verify'))
    # local progress was pushed to the account
    pg.wait_for_timeout(300)
    db = json.loads(pg.evaluate("localStorage.getItem('__fb_db')") or '{}')
    check('profile doc created', 'users/u_ada@example.com' in db)
    # signed in: gate gone, nav has account menu
    pg.goto(B + 'techbase-css/lessons/lesson_02.html'); pg.wait_for_timeout(500)
    check('lesson open when signed in', pg.locator('#gate-wall').count() == 0)
    check('account menu in nav', pg.locator('.acct-btn').count() == 1)
    # progress sync: mark a lesson on this device -> lands in db
    pg.goto(B + 'techbase-scratch/lessons/lesson_01.html'); pg.wait_for_timeout(500)
    pg.click('#mark-done'); pg.wait_for_timeout(2200)
    db = json.loads(pg.evaluate("localStorage.getItem('__fb_db')"))
    prog = db.get('progress/u_ada@example.com', {})
    check('progress saved to account', 'lesson_01.html' in prog.get('done', {}).get('techbase-scratch', []))
    check('progress made before sign-up was merged in', 'lesson_02.html' in prog.get('done', {}).get('techbase-scratch', []))
    # new device: clear tb keys, sign in again, progress comes back
    pg.evaluate("localStorage.removeItem('tb:done:techbase-scratch'); localStorage.removeItem('tb:signedin'); localStorage.removeItem('__fb_sess')")
    pg.goto(B + 'login/index.html'); pg.wait_for_selector('[data-panel="signin"]:not([hidden])')
    pg.fill('#f-email-in', 'ada@example.com'); pg.fill('#f-password', 'wrong password'); pg.click('[data-auth-form="signin"] button[type=submit]')
    pg.wait_for_selector('[data-notice]:not([hidden])'); check('wrong password message', 'do not match' in pg.inner_text('[data-notice]'))
    pg.fill('#f-password', 'correct horse battery'); pg.click('[data-auth-form="signin"] button[type=submit]')
    pg.wait_for_url('**/learn/index.html'); pg.wait_for_timeout(500)
    check('progress restored on new device', 'lesson_01.html' in (pg.evaluate("localStorage.getItem('tb:done:techbase-scratch')") or ''))
    # account page
    pg.goto(B + 'account/index.html'); pg.wait_for_selector('[data-auth-ready]:not([hidden])')
    check('account page shows name', 'Ada Lovelace' in pg.inner_text('[data-name]'))
    pg.fill('[data-account-form="profile"] [name=name]', 'Ada King'); pg.click('[data-account-form="profile"] button[type=submit]'); pg.wait_for_timeout(300)
    check('profile saved', 'Ada King' in pg.inner_text('[data-name]'))
    # contact form (signed in or not) stores a document
    pg.goto(B + 'contact/index.html')
    pg.fill('#f-name', 'Parent One'); pg.fill('#f-email', 'p@example.com'); pg.select_option('#f-who', 'Parent'); pg.fill('#f-message', 'Hello, a class for my child please.')
    pg.click('form[data-form] button[type=submit]'); pg.wait_for_selector('.form-status.is-ok')
    db = json.loads(pg.evaluate("localStorage.getItem('__fb_db')"))
    check('enquiry stored', any(k.startswith('enquiries/') for k in db))
    pg.goto(B + 'contact/index.html'); pg.click('form[data-form] button[type=submit]')
    check('empty form blocked', pg.locator('.fld.has-error').count() >= 3)
    # delete account
    pg.goto(B + 'account/index.html'); pg.wait_for_selector('[data-auth-ready]:not([hidden])')
    pg.click('[data-delete-open]'); pg.fill('#f-del-pw', 'correct horse battery'); pg.click('[data-delete-confirm]')
    pg.wait_for_url('**/index.html'); pg.wait_for_timeout(300)
    db = json.loads(pg.evaluate("localStorage.getItem('__fb_db')"))
    check('account data deleted', 'progress/u_ada@example.com' not in db and 'users/u_ada@example.com' not in db)
    pg.goto(B + 'techbase-css/lessons/lesson_02.html'); pg.wait_for_timeout(400)
    check('gate back after delete', pg.locator('#gate-wall').count() == 1)
    check('no JS errors', not errs)
    if errs: print(errs)
    b.close()
sys.exit(1 if fails else 0)
