#!/usr/bin/env python3
"""Capture UI screenshots into docs/screenshots/."""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:3000"
API = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:8000"


def main() -> None:
    from playwright.sync_api import sync_playwright

    OUT.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        page = browser.new_page(viewport={"width": 1280, "height": 800})

        page.goto(BASE, wait_until="networkidle", timeout=60_000)
        page.wait_for_selector("h1", timeout=30_000)
        page.screenshot(path=str(OUT / "01-home-upload.png"), full_page=True)

        page.get_by_role("button", name="Audio").click()
        time.sleep(0.5)
        page.screenshot(path=str(OUT / "02-home-audio.png"), full_page=True)

        page.goto(BASE, wait_until="networkidle")
        link = page.locator('a[href^="/meetings/"]').first
        if link.count():
            href = link.get_attribute("href") or ""
            link.click()
            page.wait_for_load_state("networkidle")
            page.wait_for_selector("h1", timeout=30_000)
            page.screenshot(path=str(OUT / "03-meeting-detail.png"), full_page=True)

            chat = page.get_by_role("link", name="Chat")
            if chat.count():
                chat.click()
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(2000)
                suggested = page.get_by_text("What action items were assigned?", exact=False)
                if suggested.count():
                    suggested.first.click()
                    page.wait_for_timeout(12_000)
                page.screenshot(path=str(OUT / "04-meeting-chat.png"), full_page=True)

            if href:
                page.goto(f"{BASE}{href.rstrip('/')}/intelligence", wait_until="networkidle")
                page.wait_for_timeout(5000)
                page.screenshot(path=str(OUT / "05-meeting-intelligence.png"), full_page=True)

        docs = browser.new_page(viewport={"width": 1280, "height": 900})
        docs.goto(f"{API}/docs", wait_until="networkidle", timeout=30_000)
        docs.screenshot(path=str(OUT / "06-api-docs.png"), full_page=True)

        browser.close()

    print(f"Screenshots saved to {OUT}")


if __name__ == "__main__":
    main()
