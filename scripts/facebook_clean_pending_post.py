import time
from pathlib import Path

from playwright.sync_api import sync_playwright

state_file = Path(__file__).parent.joinpath("states/facebook.json")

timeout = 60 * 100000


def get_all_groups(page):
    page.goto("https://www.facebook.com/groups/joins/?nav_source=tab", timeout=timeout)

    last_height = page.evaluate("document.body.scrollHeight")
    while True:
        page.evaluate(f"window.scrollBy(0,document.body.scrollHeight)")
        time.sleep(20)
        new_height = page.evaluate("document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    groups_links = page.locator('[role="main"] [role="list"] [role="listitem"] a') \
        .filter(has_not_text='Ver grupo')

    groups = []
    for link in groups_links.all():
        if link.text_content():
            groups.append(dict(
                url=link.get_attribute('href'),
                name=link.text_content()
            ))
    return groups


def remove_pending_content(page, group_url):
    pending_content_url = f"{group['url']}my_pending_content"
    page.goto(pending_content_url, timeout=timeout)
    print(page.inner_html())


with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False, slow_mo=1500, timeout=timeout).new_context(
        storage_state=str(state_file),
    )
    page = browser.new_page()
    groups = get_all_groups(page)

    for group in groups:
        remove_pending_content(page, group['url'])
