from django.conf import settings
import time

from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright

from facebook.models import FacebookProfile, FacebookPost


class FacebookAutomationService:
    def __init__(self, user: FacebookProfile):
        self.user = user

    def get_browser(self, pw):
        return pw.chromium.launch(**settings.PLAYWRIGHT).new_context(storage_state=self.user.context)

    def get_playwright(self):
        return sync_playwright()

    async def async_get_all_groups(self):
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(**settings.PLAYWRIGHT).new_context(storage_state=self.user.context)
            page = await browser.new_page()
            await page.goto("https://www.facebook.com/groups/")

    def get_all_groups(self):
        with self.get_playwright() as pw:
            page = self.get_browser(pw).new_page()
            page.goto("https://www.facebook.com/groups/joins/?nav_source=tab", timeout=settings.PLAYWRIGHT['timeout'])

            last_height = page.evaluate("document.body.scrollHeight")
            while True:
                page.evaluate(f"window.scrollBy(0,document.body.scrollHeight)")
                time.sleep(3)
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
            page.close()
            return groups

    def create_post(self, group_url, post: FacebookPost):
        with self.get_playwright() as pw:
            page = self.get_browser(pw).new_page()
            page.goto(group_url, timeout=settings.PLAYWRIGHT['timeout'])
            page.get_by_text('Escribe algo…').click()
            page.click('[aria-placeholder="Crea una publicación pública..."]')

            file_input = page.locator('input[type="file"][multiple]')
            file_input.set_input_files(post.file.file)
            page.keyboard.type(post.text)

            page.click('[aria-label="Publicar"]')
            page.get_by_text("Publicando", exact=True).wait_for(state='hidden', timeout=settings.PLAYWRIGHT['timeout'])
            page.close()
