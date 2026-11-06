"""Browser tests for the company-site interactions (no accounts needed). Serve dist on :8123 first."""
import sys

from playwright.sync_api import sync_playwright

B = 'http://localhost:8123/'; fails = []
def check(n, c):
    print(('PASS ' if c else 'FAIL ') + n)
    if not c: fails.append(n)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1280, 'height': 900}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(B + 'index.html'); pg.wait_for_timeout(300)
    pg.keyboard.press('Control+k'); pg.wait_for_selector('#palette[open]'); pg.keyboard.type('robotics'); pg.wait_for_timeout(300)
    check('search finds results', pg.locator('.palette-list a').count() > 2)
    pg.keyboard.press('Escape')
    pg.keyboard.press('Control+k'); pg.keyboard.type('contact'); pg.wait_for_timeout(300)
    check('search finds site pages', 'Contact' in pg.inner_text('.palette-list'))
    pg.keyboard.press('Escape')
    pg.click('#pf-tab-1'); check('path finder switches', pg.locator('#pf-panel-1').is_visible() and not pg.locator('#pf-panel-0').is_visible())
    pg.click('[data-slide="1"]'); pg.wait_for_timeout(500)
    check('slider scrolls', pg.evaluate("document.querySelector('.tslider-track').scrollLeft") > 50)
    pg.click('[data-theme-toggle]'); t1 = pg.evaluate("document.documentElement.dataset.theme"); pg.reload(); pg.wait_for_timeout(200)
    check('theme persists', pg.evaluate("document.documentElement.dataset.theme") == t1 and t1 in ('dark', 'light'))
    pg.goto(B + 'portfolio/index.html'); pg.click('[data-filter="2023"]'); pg.wait_for_timeout(200)
    check('portfolio filter', 0 < pg.locator('.pcard:visible').count() < 6)
    pg.goto(B + 'faq/index.html'); pg.fill('#faq-filter', 'certificate'); pg.wait_for_timeout(200)
    check('faq filter', pg.locator('.faq:visible').count() == 1)
    pg.goto(B + 'faq/index.html#do-you-provide-certificates'); pg.wait_for_timeout(300)
    check('faq opens from link', pg.locator('#do-you-provide-certificates[open]').count() == 1)
    pg.goto(B + 'portfolio/akinyele-spelling-challenge-2026/index.html'); pg.wait_for_timeout(300)
    n = pg.locator('[data-lightbox]').count()
    if n:
        pg.locator('[data-lightbox]').first.scroll_into_view_if_needed(); pg.locator('[data-lightbox]').first.click(); pg.wait_for_timeout(200)
        check('lightbox opens', pg.locator('#lightbox[open]').count() == 1)
    pg.goto(B + 'contact/index.html'); pg.fill('#f-name', 'x'); pg.click('form[data-form] button[type=submit]')
    check('accounts-off or on form validates', pg.locator('.fld.has-error').count() >= 2)
    pg.goto(B + 'techbase-css/index.html'); pg.wait_for_timeout(300)
    check('course page filter exists', pg.locator('#lesson-filter').count() == 1)
    pg.goto(B + 'nonexistent-page.html'); 
    check('no JS errors', not errs); print(errs)
    b.close()
sys.exit(1 if fails else 0)
