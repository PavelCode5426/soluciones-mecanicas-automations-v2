import time
from pathlib import Path

from playwright.sync_api import sync_playwright

state_file = Path(__file__).parent.joinpath("states/facebook_account_1.json")
timeout = 60 * 100000

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False, slow_mo=1500, timeout=timeout).new_context(
        storage_state=str(state_file),
    )

    page = browser.new_page()
    group_urls = ["https://www.facebook.com/groups/9307109389375863/",
                  "https://www.facebook.com/groups/1933537233825139/",
                  "https://www.facebook.com/groups/1566788557439239/"]

    for group_url in group_urls:
        page.goto(group_url, timeout=timeout)
        join_button = page.get_by_role('button', name="Unirte al grupo")
        if join_button.is_visible() and join_button.count() == 1:
            join_button.first.click()

        time.sleep(30)
