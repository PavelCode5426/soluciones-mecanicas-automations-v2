import time
from pathlib import Path

from llama_index.llms.ollama import Ollama
from playwright.sync_api import sync_playwright

host = "https://ia.pavelcode5426.duckdns.org"
model_name = "llama3.2:1b"
llm = Ollama(model=model_name, base_url=host, request_timeout=120, temperature=0.1, context_window=50_000)
with sync_playwright() as pw:
    state_file = Path(__file__).parent.joinpath("states/facebook.json")
    timeout = 60 * 100000
    browser = pw.chromium.launch(headless=False, slow_mo=500, timeout=timeout).new_context(storage_state=state_file)

    page = browser.new_page()
    page.goto('https://www.facebook.com', timeout=timeout, wait_until='networkidle', )
    write_btn = page.get_by_text('Qué estás pensando')
    write_btn.wait_for(state='visible')
    write_btn.click()

    attempts = 3
    dialog = page.get_by_role('dialog').first
    while attempts > 0:
        if dialog.is_visible():
            break
        write_btn.click()
        attempts -= 1

    publicar_btn = dialog.locator('[aria-label="Publicar"]')
    publicar_btn.wait_for(state='visible')

    response = llm.complete("Genera una historia para Facebook sobre un tema interesante. Dame solo el texto para "
                            "escribir.")
    page.keyboard.type(response.text)
    time.sleep(3)
    publicar_btn.click()
    page.locator('span', has_text='Publicando').wait_for(state='hidden')
