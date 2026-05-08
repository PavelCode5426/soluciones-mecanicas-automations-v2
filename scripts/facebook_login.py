from pathlib import Path

from playwright.sync_api import sync_playwright

username = "social.account@solucioneshevia.com"
password = "@B123456*"

state_file = Path(__file__).parent.joinpath("states/facebook_account_1.json")
timeout = 60 * 100000
with sync_playwright() as pw:
    device = pw.devices['iPhone 8']
    browser = pw.chromium.launch(
        headless=False, slow_mo=500, timeout=timeout, chromium_sandbox=False,
        # proxy={
        #     "server": "http://pavelcode5426.duckdns.org:8888",
        #     "username": "pavelcode5426",
        #     "password": "pavelcode5426"
        # },
        args=[
            # '--disable-blink-features=AutomationControlled',
            '--disable-blink-features',
            '--disable-web-security',
            # '--disable-infobars', '--disable-extensions', '--start-maximized',
            # '--disable-features=IsolateOrigins,site-per-process'
        ]
    ).new_context(storage_state=state_file)

    page = browser.new_page()
    page.goto('https://www.facebook.com/', timeout=timeout)
    active = not bool(page.locator('text=Iniciar sesión').count())
    page.wait_for_load_state('networkidle', timeout=timeout)

    if not active:
        page.locator('[name="email"]').click()
        page.keyboard.type(username)
        page.locator('[name="pass"]').click()
        page.keyboard.type(password)
        page.keyboard.press('Enter')

    page.wait_for_load_state('networkidle', timeout=timeout)
    input("Continuar...")
    browser.storage_state(path=state_file)
