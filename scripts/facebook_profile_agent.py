import random
import time
from pathlib import Path

from llama_index.llms.ollama import Ollama
from playwright.sync_api import sync_playwright

host = "https://ia.pavelcode5426.duckdns.org"
model_name = "llama3.2:1b"
llm = Ollama(model=model_name, base_url=host, request_timeout=120, temperature=0.1, context_window=50_000)
with sync_playwright() as pw:
    state_file = Path(__file__).parent.joinpath("states/accounts/account_1.json")
    timeout = 60 * 100000
    browser = pw.chromium.launch(headless=False, slow_mo=500, timeout=timeout).new_context(storage_state=state_file)

    page = browser.new_page()
    page.goto('https://www.facebook.com/', timeout=timeout)
    page.get_by_text('Reels').click()
    # page.get_by_role('link').and_(page.locator('[aria-label="Reels"]')).click()

    watch_time = random.randint(5 * 60, 10 * 60)
    start_time = time.time()

    while time.time() - start_time < watch_time:
        time.sleep(random.randint(5, 30))
        if random.choice([True, False]):
            try:
                page.get_by_role('button').and_(page.locator('[aria-label="Me gusta"][tabindex="0"]')).click()
            except:
                pass
            if random.choice([True, False]):
                page.get_by_role('button').and_(page.locator('[aria-label="Compartir"][tabindex="0"]')).click()
                page.get_by_text(random.choice(["Compartir ahora","Historia"])).click()

        page.keyboard.press('ArrowDown')
