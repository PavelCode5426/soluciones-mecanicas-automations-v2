from playwright.sync_api import sync_playwright

state_file = "states/revolico.json"
timeout = 60 * 100000
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False, slow_mo=500,
                                args=[
                                    '--disable-blink-features=AutomationControlled',
                                    '--no-sandbox', '--disable-web-security',
                                    '--disable-infobars', '--disable-extensions', '--start-maximized',
                                    '--window-size=1280,720'
                                ]).new_context(storage_state=state_file)

    page = browser.new_page()
    page.goto("https://revolico.com", timeout=timeout)
    input("Continuar...")
    browser.storage_state(path=state_file)
