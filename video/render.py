"""Render scene.html to MP4.

  python render.py preview 3 10 29 38     -> stills at those seconds (preview_*.jpg)
  python render.py                        -> full video (needs music.wav from music.py)
"""
import pathlib
import subprocess
import sys

import imageio_ffmpeg
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).parent
SCENE = (HERE / "scene.html").resolve().as_uri()
FPS = 30
OUT = HERE / "感谢老师·三年.mp4"


def open_scene(p):
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    page.goto(SCENE, wait_until="networkidle")
    page.evaluate("window.ready")
    page.wait_for_timeout(500)
    return browser, page


def preview(times):
    with sync_playwright() as p:
        browser, page = open_scene(p)
        for t in times:
            page.evaluate(f"seek({t})")
            page.screenshot(path=str(HERE / f"preview_{t}.jpg"), type="jpeg", quality=85)
        browser.close()


def render():
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    with sync_playwright() as p:
        browser, page = open_scene(p)
        duration = page.evaluate("window.DURATION")
        frames = int(duration * FPS)
        cmd = [
            ffmpeg, "-y", "-loglevel", "error",
            "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
            "-i", str(HERE / "music.wav"),
            "-vf", "scale=in_range=pc:out_range=tv,format=yuv420p", "-color_range", "tv",
            "-c:v", "libx264", "-preset", "slow", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
            str(OUT),
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(frames):
            page.evaluate(f"seek({i / FPS})")
            proc.stdin.write(page.screenshot(type="jpeg", quality=95))
            if i % 150 == 0:
                print(f"frame {i}/{frames}", flush=True)
        proc.stdin.close()
        proc.wait()
        browser.close()
    print("done")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        preview([float(x) for x in sys.argv[2:]])
    else:
        render()
