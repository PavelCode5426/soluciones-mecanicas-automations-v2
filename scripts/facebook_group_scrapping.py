import asyncio
import random
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from scripts.automations import FacebookPostAnalyzerAgent, run_async

state_file = Path(__file__).parent.joinpath("states/facebook.json")
timeout = 60 * 100000

with sync_playwright() as pw:
    device = pw.devices['iPhone 12']
    browser = pw.chromium.launch(headless=False, slow_mo=1500, timeout=timeout).new_context(
        storage_state=str(state_file),
        # viewport={"width": 390, "height": 644},
        # record_video_dir="videos/", record_video_size={"width": 390, "height": 644}
    )

    page = browser.new_page()
    group_url = [
        # GRUPO DE VENTAS DE 360
        "https://www.facebook.com/groups/614763077230692/",
    ]
    page.goto(random.choice(group_url), timeout=timeout, wait_until='commit')

    facebook_articles = []
    seen_ids = set()
    attemps = 1
    count = 0

    while count <= 1:
        articles_locator = page.locator("div[aria-posinset]")
        count = articles_locator.count()
        if count > 0:
            page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
        time.sleep(3)

    i = 0
    while i < count and i < 100:
        article = articles_locator.nth(i)
        article.scroll_into_view_if_needed(timeout=timeout)
        article.wait_for(state="visible")

        try:
            button = article.get_by_role("button", name="Ver más")
            if button.is_visible():
                button.click()
        except Exception:
            pass

        post_html = article.inner_html()


        async def analyzer_facebook_post():
            textarea = article.get_by_text("Comentar como")

            post_analyser = FacebookPostAnalyzerAgent()
            # response = await post_analyser.run(raw_html=post_html)
            # if response.is_relevant:
            if True:
                textarea.click()
                # page.keyboard.type(response.promotional_message)
                page.keyboard.type("Hola")
                page.keyboard.press('Enter')


        run_async(analyzer_facebook_post())
        # page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
        count = articles_locator.count()
        browser.storage_state(path=state_file)
        i += 1
