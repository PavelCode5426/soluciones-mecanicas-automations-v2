from pathlib import Path

from playwright.sync_api import sync_playwright

username = "social.account@solucioneshevia.com"
password = "@B123456*"

account_number = f"account_{input('Numero de cuenta: ')}"

state_file = Path(__file__).parent.joinpath(f"states/accounts/{account_number}.json")
state_file = Path(__file__).parent.joinpath(f"states/facebook.json")
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
    continue_button = page.get_by_text("Continuar")
    if continue_button.is_visible():
        continue_button.click()
        page.wait_for_load_state('load')

    active = not bool(page.locator('text=Iniciar sesión').count())
    if active:
        dialog = page.get_by_role('dialog')
        if dialog.is_visible():
            close_btn = dialog.locator('[aria-label*="Cerrar"]')
            close_btn.wait_for(state='visible')
            close_btn.click()
    # page.wait_for_load_state('networkidle', timeout=timeout)

    # if not active:
    #     if page.locator('[name="email"]').count() > 0:
    #         page.locator('[name="email"]').click()
    #         page.keyboard.type(username)
    #     page.locator('[name="pass"]').click()
    #     page.keyboard.type(password)
    #     page.keyboard.press('Enter')

    # page.wait_for_load_state('networkidle', timeout=timeout)
    input("Continuar...")
    browser.storage_state(path=state_file)
