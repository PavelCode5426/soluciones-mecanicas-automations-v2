from pathlib import Path

from playwright.sync_api import sync_playwright

state_file = Path(__file__).parent.joinpath("states/facebook.json")

url = ''
timeout = 60 * 100000
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False, slow_mo=500, timeout=timeout).new_context(storage_state=state_file)

    page = browser.new_page()
    page.goto("https://www.facebook.com/groups/ventasencuba/", wait_until='networkidle', timeout=timeout)
    write_btn = page.get_by_role('button').get_by_text('Escribe algo')
    write_btn.wait_for(state='visible')
    write_btn.click()

    dialog = page.get_by_role('dialog')
    dialog.wait_for(state='visible')

    publicar_btn = dialog.get_by_role('button').get_by_text('Publicar')
    publicar_btn.wait_for(state='visible')
    page.keyboard.insert_text("Hola")
    page.keyboard.press('Enter')
    page.keyboard.insert_text("Hola")
