import random
import time
from pathlib import Path

import requests
from huggingface_hub import InferenceClient
from llama_index.llms.ollama import Ollama
from playwright.sync_api import sync_playwright

from scripts.automations import FacebookAccountAgent

state_file = Path(__file__).parent.joinpath("states/facebook.json")
timeout = 60 * 100000
api_key = ""
host = "https://ia.pavelcode5426.duckdns.org"
model_name = "llama3.2:1b"
model_name = "llama3.1:8b-instruct-q4_K_M"

llm = Ollama(model=model_name, base_url=host, request_timeout=120, temperature=0.1, context_window=50_000)
inference_client = InferenceClient(provider="hf-inference", api_key=api_key)

profile_agent = FacebookAccountAgent(llm, inference_client)

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False, slow_mo=500, timeout=timeout).new_context(storage_state=state_file)
    page = browser.new_page()

    # page.goto('https://www.facebook.com/friends/list', timeout=timeout, wait_until='load')
    # more_buttons = page.get_by_role('button').and_(page.locator('[aria-label="Más"]'))
    # while more_buttons.count():
    #     more_buttons.first.click()
    #     page.get_by_text("Eliminar").first.click()
    #     page.get_by_text("Confirmar").first.click()

    page.goto('https://www.facebook.com/friends', timeout=timeout, wait_until='load')
    account_list = page.get_by_role('main')
    accounts = account_list.get_by_role('listitem')

    index = 0
    for_send = 100

    while for_send < accounts.count():
        accounts.last.scroll_into_view_if_needed()

    while index < for_send:
        account = accounts.nth(index)
        account.highlight()

        raw_html = account.inner_html()
        response = profile_agent.could_be_friend(raw_html)

        delete_button = account.get_by_role('button').get_by_text("Eliminar")

        text = account.inner_text()
        if any(x in text for x in ['cuenta', 'común']) or random.choice([True, False, False, False, False]):
            image = account.locator('img').get_attribute('src')

            if profile_agent.is_nsfw_image(image):
                account.get_by_role('button').get_by_text("Agregar a amigos").click()
                time.sleep(3)
                index += 1
                continue
        delete_button.click()
