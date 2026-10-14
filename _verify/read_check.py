"""Verify the read-aloud button, the AI notice modal and per-language playback.

  python read_check.py            -> bundled chromium
  python read_check.py msedge     -> installed Edge (has MP3 codecs)
"""
import pathlib
import sys

from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).parent
PAGE = (HERE.parent / "index.html").resolve().as_uri()
CHANNEL = sys.argv[1] if len(sys.argv) > 1 else None


def probe(page, tag):
    s = page.evaluate(
        """() => {
             const btn = document.getElementById('readBtn');
             return {cls: btn.className,
                     label: btn.querySelector('.read-label').textContent,
                     modal: document.getElementById('noticeModal').classList.contains('is-open'),
                     progress: document.getElementById('readProgress').style.width || '0%'};
           }"""
    )
    print(f"  [{tag}] label={s['label']!r} class={s['cls']!r} modal={s['modal']} progress={s['progress']}")
    return s


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, channel=CHANNEL) if CHANNEL else p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.goto(PAGE, wait_until="networkidle")

    print("1) 初始状态")
    probe(page, "init")

    print("2) 点朗读 -> 应弹温馨提醒")
    page.eval_on_selector("#readBtn", "el => el.click()")
    page.wait_for_timeout(600)
    probe(page, "after click")
    page.screenshot(path=str(HERE / "notice_modal.png"))

    print("3) 点『我明白了，开始播放』-> 应真的开始播")
    page.eval_on_selector("#noticeOk", "el => el.click()")
    page.wait_for_timeout(4500)
    s = probe(page, "playing")
    page.screenshot(path=str(HERE / "read_playing.png"))

    print("4) 切到泰米尔文 -> 应停止中文朗读并换上泰米尔文标签")
    page.click('.lang-btn[data-lang="ta"]')
    page.wait_for_timeout(500)
    probe(page, "ta")

    print("5) 泰米尔文点朗读 -> 弹窗 -> 确认 -> 应播放 voice/hl voice.mp3")
    page.eval_on_selector("#readBtn", "el => el.click()")
    page.wait_for_timeout(400)
    probe(page, "ta notice")
    page.screenshot(path=str(HERE / "notice_modal_ta.png"))
    page.eval_on_selector("#noticeOk", "el => el.click()")
    page.wait_for_timeout(4000)
    probe(page, "ta playing")
    page.screenshot(path=str(HERE / "read_ta_playing.png"))

    print("6) 回中文，确认播放后点音乐 -> 朗读应被自动暂停（两者互斥）")
    # The page ships with an empty #bgm, so give it a source first — otherwise the
    # music handler returns early and never reaches the "pause the reading" branch.
    page.evaluate(
        """() => { const b = document.getElementById('bgm');
                   b.innerHTML = '<source src="video/music.wav" type="audio/wav">'; }"""
    )
    page.click('.lang-btn[data-lang="zh"]')
    page.wait_for_timeout(300)
    page.eval_on_selector("#readBtn", "el => el.click()")
    page.wait_for_timeout(400)
    page.eval_on_selector("#noticeOk", "el => el.click()")
    page.wait_for_timeout(3000)
    probe(page, "zh playing")
    page.eval_on_selector("#musicToggle", "el => el.click()")
    page.wait_for_timeout(1200)
    probe(page, "music on")

    print("7) 勾『不再显示此提醒』后 -> 以后点朗读应直接播、不再弹窗")
    page.eval_on_selector("#musicToggle", "el => el.click()")   # 关掉音乐
    page.wait_for_timeout(300)
    page.eval_on_selector("#readBtn", "el => el.click()")       # 暂停朗读
    page.wait_for_timeout(200)
    page.reload(wait_until="networkidle")
    page.eval_on_selector("#readBtn", "el => el.click()")       # 重新点：会弹窗
    page.wait_for_timeout(400)
    page.check("#noticeSkip")
    page.eval_on_selector("#noticeOk", "el => el.click()")
    page.wait_for_timeout(2500)
    probe(page, "skip set, playing")
    page.eval_on_selector("#readBtn", "el => el.click()")       # 暂停
    page.wait_for_timeout(300)
    page.eval_on_selector("#readBtn", "el => el.click()")       # 再点：应无需弹窗
    page.wait_for_timeout(1200)
    probe(page, "second click, no modal")

    browser.close()

print("done" if not CHANNEL else f"done ({CHANNEL})")
