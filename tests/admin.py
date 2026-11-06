"""Browser tests for the blog admin area, against a build made with tests/bundle_fake.mjs (fake Firebase, fake Firestore web address).
Run after tests/e2e.py setup: node tests/bundle_fake.mjs && FIREBASE_API_KEY=AIzaFakeKey1234567890 ... python3 build/build.py && python3 -m http.server -d dist 8123 & python3 tests/admin.py"""
import base64
import json
import struct
import sys
import zlib

from playwright.sync_api import sync_playwright

B = 'http://localhost:8123/'
fails = []
def check(name, cond):
    print(('PASS ' if cond else 'FAIL ') + name)
    if not cond: fails.append(name)

def png(w=40, h=30):
    raw = b''.join(b'\x00' + bytes([200, 80, 40]) * w for _ in range(h))
    def chunk(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')

SNAP = {}
def fields(d): return {k: ({'booleanValue': v} if isinstance(v, bool) else {'stringValue': str(v)}) for k, v in d.items() if v is not None}
def rest(route):
    url = route.request.url
    if ':runQuery' in url:
        rows = [{'document': {'name': f'projects/demo/databases/(default)/documents/{k}', 'fields': fields(v)}} for k, v in SNAP.items() if k.startswith('posts/') and v.get('published') is True]
        return route.fulfill(json=rows or [{'readTime': 'x'}], headers={'access-control-allow-origin': '*'})
    key = url.split('/documents/')[1].split('?')[0]
    if key in SNAP:
        return route.fulfill(json={'name': 'projects/demo/databases/(default)/documents/' + key, 'fields': fields(SNAP[key])}, headers={'access-control-allow-origin': '*'})
    return route.fulfill(status=404, json={'error': {}}, headers={'access-control-allow-origin': '*'})

def seed(pg, email, admin):
    pg.goto(B + 'index.html')
    pg.evaluate("""([email, admin]) => {
      localStorage.setItem('__fb_users', JSON.stringify({[email]: {uid: 'u_' + email, email, pw: 'pw123456', name: 'Ada Admin', verified: true}}));
      localStorage.setItem('__fb_sess', JSON.stringify(email));
      const db = JSON.parse(localStorage.getItem('__fb_db') || '{}');
      if (admin) db['admins/u_' + email] = {};
      localStorage.setItem('__fb_db', JSON.stringify(db));
    }""", [email, admin])

def snap(pg):
    SNAP.clear(); SNAP.update(json.loads(pg.evaluate("localStorage.getItem('__fb_db')") or '{}'))

with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={'width': 1280, 'height': 900}); pg = ctx.new_page()
    ctx.route('https://firestore.googleapis.com/**', rest)
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    # signed out
    pg.goto(B + 'admin/index.html'); pg.wait_for_selector('[data-view="signin"]:not([hidden])')
    check('signed-out visitor is asked to sign in', True)
    check('admin page is noindex', 'noindex' in pg.locator('meta[name=robots]').get_attribute('content'))
    # signed in but not an administrator
    seed(pg, 'visitor@example.com', False)
    pg.goto(B + 'admin/index.html'); pg.wait_for_selector('[data-view="denied"]:not([hidden])')
    check('non-admin sees their account ID', pg.inner_text('[data-uid]') == 'u_visitor@example.com')
    check('non-admin cannot see editor', pg.locator('[data-view="editor"]:not([hidden])').count() == 0)
    # administrator writes a post
    seed(pg, 'ada@example.com', True)
    pg.goto(B + 'admin/index.html'); pg.wait_for_selector('[data-view="list"]:not([hidden])')
    check('empty list message', pg.locator('[data-empty].is-visible').count() == 1)
    pg.click('[data-new]'); pg.wait_for_selector('[data-view="editor"]:not([hidden])')
    pg.click('form.editor button[type=submit]')
    check('empty post is blocked', pg.locator('.editor .has-error').count() >= 3)
    pg.fill('#ed-title', 'Our First Admin Post')
    check('address is filled from title', pg.input_value('#ed-slug') == 'our-first-admin-post')
    pg.fill('#ed-summary', 'A short summary of the post.')
    pg.fill('#ed-body', 'Hello **world**.\n\n## A heading\n\n- one\n- two\n\n[Contact](/contact/) <script>window.__pwned=1</script> [bad](javascript:alert(1))')
    pg.wait_for_timeout(300)
    check('preview renders bold + heading + list', pg.locator('[data-preview] strong').count() == 1 and pg.locator('[data-preview] h2').count() == 1 and pg.locator('[data-preview] li').count() == 2)
    check('preview has no script and blocks javascript: links', pg.locator('[data-preview] script').count() == 0 and 'javascript:' not in (pg.evaluate("[...document.querySelectorAll('[data-preview] a')].map(a=>a.getAttribute('href')).join(' ')")))
    # library photo as cover
    pg.click('[data-pick-cover]'); pg.wait_for_selector('#lib-dialog[open] [data-lib-grid] button')
    pg.click('#lib-dialog [data-lib-grid] button >> nth=0')
    check('cover from library shows', pg.locator('[data-cover-preview] img').count() == 1)
    # upload a photo inside the article
    pg.click('[data-md="upload"]'); pg.wait_for_selector('#up-dialog[open]')
    pg.set_input_files('#up-file', {'name': 'x.png', 'mimeType': 'image/png', 'buffer': png()}); pg.wait_for_selector('[data-up-preview] img')
    pg.click('[data-up-add]')
    check('alt text required for uploads', 'Describe' in pg.inner_text('#e-up-alt'))
    pg.fill('#up-alt', 'An orange test picture'); pg.click('[data-up-add]'); pg.wait_for_selector('#up-dialog', state='hidden')
    check('upload inserted into article', '(img:' in pg.input_value('#ed-body'))
    pg.check('#ed-published'); pg.click('form.editor button[type=submit]'); pg.wait_for_selector('[data-view="list"]:not([hidden]) [data-post-list] li')
    snap(pg)
    post = SNAP.get('posts/our-first-admin-post', {})
    check('post saved as published', post.get('published') is True and post.get('title') == 'Our First Admin Post')
    check('image saved separately', any(k.startswith('postImages/') and v['data'].startswith('data:image/') for k, v in SNAP.items()))
    check('list shows the post', 'Our First Admin Post' in pg.inner_text('[data-post-list]'))
    # public pages read it without signing in
    pg2 = ctx.new_page(); pg2.on('pageerror', lambda e: errs.append(str(e)))
    pg2.goto(B + 'blog/index.html'); pg2.wait_for_selector('[data-live-list] [data-slug="our-first-admin-post"]', timeout=5000)
    check('new post card on the blog index', True)
    pg2.goto(B + 'blog/post/index.html?s=our-first-admin-post'); pg2.wait_for_selector('[data-lp-article]:not([hidden])')
    check('live page shows title', pg2.inner_text('[data-lp-title]') == 'Our First Admin Post')
    check('live page renders markdown safely', pg2.locator('[data-lp-body] strong').count() == 1 and pg2.locator('[data-lp-body] script').count() == 0 and pg2.evaluate('window.__pwned') is None)
    pg2.wait_for_selector('[data-lp-body] figure img[src^="data:image/"]', timeout=5000)
    check('uploaded picture displays', True)
    pg2.goto(B + 'blog/post/index.html?s=does-not-exist'); pg2.wait_for_selector('[data-lp-state]:not([hidden])')
    check('missing post says so', 'could not find' in pg2.inner_text('[data-lp-state]'))
    # edit, unpublish, delete
    pg.click('[data-edit="our-first-admin-post"]'); pg.wait_for_selector('[data-view="editor"]:not([hidden])')
    check('slug locked when editing', pg.get_attribute('#ed-slug', 'readonly') is not None)
    pg.fill('#ed-title', 'Our First Admin Post (edited)'); pg.uncheck('#ed-published'); pg.click('form.editor button[type=submit]')
    pg.wait_for_selector('[data-view="list"]:not([hidden]) [data-post-list] li'); snap(pg)
    check('edit saved as draft', SNAP['posts/our-first-admin-post']['published'] is False and 'edited' in SNAP['posts/our-first-admin-post']['title'])
    pg2.goto(B + 'blog/post/index.html?s=our-first-admin-post'); pg2.wait_for_selector('[data-lp-state]:not([hidden])')
    check('draft is not public', 'could not find' in pg2.inner_text('[data-lp-state]'))
    pg.click('[data-edit="our-first-admin-post"]'); pg.wait_for_selector('[data-view="editor"]:not([hidden])')
    pg.click('[data-delete]'); pg.click('[data-del-confirm]'); pg.wait_for_selector('[data-empty].is-visible'); snap(pg)
    check('post and its images deleted', not any(k.startswith('posts/') or k.startswith('postImages/') for k in SNAP))
    check('no JS errors', not errs)
    if errs: print(errs)
    b.close()
sys.exit(1 if fails else 0)
