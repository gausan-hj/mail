"""Verify the four-language switcher on index.html: open the letter in each language and screenshot."""
import pathlib

from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).parent
PAGE = (HERE.parent / "index.html").resolve().as_uri()
LANGS = ["zh", "ms", "en", "ta"]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    # 1. closed state (shows the language switcher itself)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.goto(PAGE, wait_until="networkidle")
    page.wait_for_timeout(2500)
    page.screenshot(path=str(HERE / "lang_closed.png"))
    page.close()

    # 2. opened letter, one screenshot per language
    for lang in LANGS:
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(PAGE, wait_until="networkidle")
        page.click(f'.lang-btn[data-lang="{lang}"]')
        page.click("#openBtn")
        page.wait_for_timeout(5600)
        page.screenshot(path=str(HERE / f"lang_{lang}.png"))
        title = page.eval_on_selector(".letter-title", "el => el.textContent")
        cta = page.eval_on_selector("#closeBtn", "el => el.textContent")
        html_lang = page.evaluate("document.documentElement.lang")
        # The long letter is meant to scroll vertically; horizontal overflow is the
        # real defect signal (content wider than the sheet = clipped text).
        m = page.eval_on_selector(
            "#letter",
            "el => ({hOver: el.scrollWidth - el.clientWidth, vScroll: el.scrollHeight - el.clientHeight})",
        )
        print(
            f"{lang:3} html.lang={html_lang:6} title={title!r} close={cta!r} "
            f"hOverflowPx={m['hOver']} vScrollablePx={m['vScroll']}"
        )
        page.close()

    browser.close()
print("done")
