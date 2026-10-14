"""Verify one or more languages of the letter: paragraph count, scroll, hint, close.

  python letter_check.py            -> zh
  python letter_check.py ms en ta   -> those languages
"""
import pathlib
import sys

from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).parent
PAGE = (HERE.parent / "index.html").resolve().as_uri()
LANGS = sys.argv[1:] or ["zh"]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for lang in LANGS:
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(PAGE, wait_until="networkidle")
        page.click(f'.lang-btn[data-lang="{lang}"]')
        # .cta breathes forever, so Playwright's "element is stable" check never
        # passes — dispatch the click directly instead.
        page.eval_on_selector("#openBtn", "el => el.click()")
        page.wait_for_timeout(5600)
        n = page.eval_on_selector_all("#letterBody p", "els => els.length")
        box = page.eval_on_selector("#letter", "el => ({sh: el.scrollHeight, ch: el.clientHeight})")
        title = page.eval_on_selector(".letter-title", "el => el.textContent")
        sub = page.eval_on_selector(".letter-sub", "el => el.textContent")
        first = page.eval_on_selector("#letterBody p", "el => el.textContent")
        last = page.eval_on_selector("#letterBody p:last-child", "el => el.textContent")
        sign = page.eval_on_selector(".letter-sign", "el => el.textContent")
        hint = page.eval_on_selector("#scrollHint", "el => getComputedStyle(el).opacity")
        print(f"[{lang}] paras={n} box={box} hintOpacity={hint}")
        print(f"     title={title!r}\n     sub={sub!r}\n     first={first!r}\n     last={last!r}\n     sign={sign!r}")
        page.screenshot(path=str(HERE / f"letter_{lang}_top.png"))
        page.eval_on_selector("#letter", "el => el.scrollTop = el.scrollHeight")
        page.wait_for_timeout(900)
        page.screenshot(path=str(HERE / f"letter_{lang}_bottom.png"))
        page.eval_on_selector("#closeBtn", "el => el.click()")
        page.wait_for_timeout(5600)
        print(f"     closed -> letter.class={page.eval_on_selector('#letter', 'el => el.className')!r}")
        page.close()
    browser.close()
print("done")
