import random
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
    page.goto('https://www.facebook.com/stories/create/', timeout=timeout, wait_until='load')

    text_history_button = page.get_by_text("Crear una historia de texto")
    image_history_button = page.get_by_text("Crear una historia con foto")

    is_text_history = True
    if is_text_history:
        text_history_button.click()
        page.locator('[aria-controls="StoriesCreateSATPFontMenu"]').click()
        fonts = page.locator('#StoriesCreateSATPFontMenu').get_by_role('button')
        fonts.first.wait_for(state='visible')
        random.choice(fonts.all()).click()

        page.locator('[aria-label*="Más fondos"]').click()
        gradient_color = page.locator('[aria-label*="imagen de fondo"]').all()
        random.choice(gradient_color).click()
        page.locator('[aria-label="Story text"]').click()

        response = llm.complete("Genera una historia para Facebook sobre un tema interesante. Dame solo el texto para "
                                "escribir. Debe tener un maximo de 200 caracteres")
        page.keyboard.type(response.text)
    else:
        with page.expect_file_chooser() as fc:
            image_history_button.click()
        file_chooser = fc.value
        file = Path(__file__).parent.joinpath("data/picture.jpg")
        file_chooser.set_files(file)

    page.get_by_text("Compartir").click()
    page.locator("span", has_text="Publicando").wait_for(state='hidden')
