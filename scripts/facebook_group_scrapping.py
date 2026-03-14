import asyncio
import random
import time
from pathlib import Path

from ia_assistant.agents.workflows import FacebookPostAnalyzerAgent
from services.automations import get_playwright

state_file = Path(__file__).parent.joinpath("states/facebook.json")
timeout = 60 * 100000

comment_template = "Hola {name}, cansad@ de publicar y compartir a diario? 🚀 Automatiza con nosotros y consigue resultados comprobados. Nuestro sistema publica de forma automática en múltiples grupos de Facebook y Revolico, aumentando el alcance de tu negocio sin esfuerzo. Contáctanos al +5354266836 o al +5355579761. Somos un equipo especializado en software y marketing para emprendedores y grandes empresas. 📞 ¡Solicita una demostración gratuita hoy mismo y descubre cómo podemos hacer crecer tu negocio sin complicaciones!"

with get_playwright() as pw:
    browser = pw.chromium.launch(headless=False, slow_mo=500, timeout=timeout).new_context(
        storage_state=str(state_file))

    page = browser.new_page()
    group_url = [
        # GRUPO DE VENTAS DE 360
        # "https://www.facebook.com/groups/614763077230692/",
        "https://www.facebook.com/groups/128790920317347/"
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
            textarea = article.get_by_role('textbox')
            post_analyser = FacebookPostAnalyzerAgent()
            response = await post_analyser.run(raw_html=post_html)

            if response.is_relevant:
                textarea.click()
                page.keyboard.type(response.promotional_message)
                page.keyboard.press('Enter')


        loop = asyncio.get_running_loop()
        try:
            loop.run_until_complete(analyzer_facebook_post())
        except Exception as e:
            pass
        # page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
        count = articles_locator.count()
        browser.storage_state(path=state_file)
        i += 1
