import random
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from scripts.automations import FacebookPostAnalyzerAgent, run_async

state_file = Path(__file__).parent.joinpath("states/facebook.json")
timeout = 60 * 100000

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False, slow_mo=1500, timeout=timeout).new_context(
        storage_state=str(state_file),
    )

    page = browser.new_page()
    group_url = ["https://www.facebook.com/groups/search/group_posts", None]
    search_keyword = "Pollo en venta"

    group_url = random.choice(group_url)

    url = group_url if group_url else f'https://www.facebook.com/search/top/'
    if search_keyword:
        url += f'?q={search_keyword}'
    page.goto(url, wait_until='commit')

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
            lead_description = """Soy Ivonne, comercial de una empresa mayorista de alimentos. Vendo pollo y productos Vima a 
                los mejores precios, con servicio de transporte incluido. Busco dueños de negocios de alimentos (
                restaurantes, pollerías, supermercados, tiendas) que necesiten proveedor mayorista y quieran entrar a mi 
                cartera de clientes. Escribirme al privado por teléfono +53 55161004"""

            post_analyser = FacebookPostAnalyzerAgent(lead_description=lead_description)
            response = await post_analyser.run(raw_html=post_html)

            if response.is_relevant:
                article.locator('[aria-label="Dejar un comentario"]').click()

                modal = page.get_by_role('dialog')

                textarea = modal.get_by_text("Comentar como")
                textarea.scroll_into_view_if_needed()
                textarea.highlight()
                textarea.click(force=True)

                page.keyboard.type(response.promotional_message)
                page.keyboard.press('Enter')

                modal.locator('[aria-label="Cerrar"]').click()


        run_async(analyzer_facebook_post())
        # page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
        count = articles_locator.count()
        browser.storage_state(path=state_file)
        i += 1
