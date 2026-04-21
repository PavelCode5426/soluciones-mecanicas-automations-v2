import time
from pathlib import Path

from playwright.sync_api import sync_playwright

state_file = Path(__file__).parent.joinpath("states/facebook.json")

url = "https://www.facebook.com/groups/1116295636394497/"

post_title = "Neveras en venta"

post_text = """
Publicación de prueba
"""

post_hastag = """
#pizza
"""
post_footer = """

"""
post_file = Path(__file__).parent.joinpath("data/1.jpg")

timeout = 60 * 100000
with sync_playwright() as pw:
    device = pw.devices['iPhone 12']
    browser = pw.chromium.launch(headless=False, slow_mo=1500, timeout=timeout).new_context(
        storage_state=str(state_file),
        # viewport={"width": 390, "height": 644},
        # record_video_dir="videos/", record_video_size={"width": 390, "height": 644}
    )
    # browser = pw.chromium.launch(headless=False, slow_mo=500, timeout=timeout).new_context(storage_state=state_file)

    page = browser.new_page()
    page.goto(url, wait_until='load', timeout=timeout)
    write_btn = page.get_by_text('Escribe algo')
    write_btn.wait_for(state='visible')
    write_btn.click()

    attempts = 3
    dialog = page.get_by_role('dialog').first
    while attempts > 0:
        if dialog.is_visible():
            break
        write_btn.click()
        attempts -= 1
    # dialog.wait_for(state='visible')

    publicar_btn = dialog.locator('[aria-label="Publicar"]')
    publicar_btn.wait_for(state='visible')

    if post_file:
        file_input = page.locator('input[type="file"][multiple]').first
        file_input.set_input_files(files=[post_file])

    page.keyboard.type(post_title)
    page.keyboard.press('Enter')
    page.keyboard.type(post_text)
    page.keyboard.press('Enter')
    page.keyboard.press('Enter')
    page.keyboard.type(post_footer)
    page.keyboard.press('Enter')
    page.keyboard.press('Enter')

    hashtags = post_hastag.split("\n")
    for hastag in hashtags:
        page.keyboard.type(hastag.strip())
        page.keyboard.press('Enter')
        page.keyboard.press("Space")

    time.sleep(3)
    publicar_btn.click()
    page.locator('span', has_text='Publicando').wait_for(state='hidden')
    input("")
