from playwright.sync_api import sync_playwright

state_file = "states/facebook.json"
timeout = 60 * 100000
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False, slow_mo=500, timeout=timeout).new_context(storage_state=state_file)

    page = browser.new_page()
    page.goto('https://www.facebook.com/', timeout=timeout)
    active = not bool(page.locator('text=Iniciar sesión').count())
    print(active)
    input("Continuar...")
    browser.storage_state(path=state_file)
