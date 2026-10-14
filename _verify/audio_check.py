"""Compare each language's letter length with its voice-over duration."""
import pathlib

from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).parent
PAGE = (HERE.parent / "index.html").resolve().as_uri()

# durations probed with ffmpeg (seconds)
DUR = {"zh": 21 * 60 + 22.12, "ms": 8 * 60 + 49.48, "en": 6 * 60 + 13.71, "hl": 8 * 60 + 27.01}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(PAGE, wait_until="networkidle")
    stats = {}
    for lang in ("zh", "ms", "en", "ta"):
        page.click(f'.lang-btn[data-lang="{lang}"]')
        stats[lang] = page.evaluate(
            """() => {
                 const ps = [...document.querySelectorAll('#letterBody p')];
                 const text = ps.map(p => p.textContent).join('');
                 return {paras: ps.length, chars: text.length,
                         words: text.split(/\\s+/).filter(Boolean).length};
               }"""
        )
    browser.close()

print(f"{'lang':5}{'paras':>7}{'chars':>9}{'words':>8}{'duration':>11}{'chars/s':>9}")
for lang, s in stats.items():
    dur = DUR.get(lang)
    cps = f"{s['chars'] / dur:.1f}" if dur else "-"
    print(f"{lang:5}{s['paras']:>7}{s['chars']:>9}{s['words']:>8}{(f'{dur:.0f}s' if dur else '-'):>11}{cps:>9}")
