import time

from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.files.base import ContentFile
from playwright.sync_api import sync_playwright, PlaywrightContextManager, Playwright

from facebook.models import FacebookProfile, FacebookPost, FacebookGroup


class FacebookAutomationService:
    def __init__(self, user: FacebookProfile):
        self.user = user

    def get_browser(self, pw: Playwright):
        return pw.chromium.launch(**settings.PLAYWRIGHT).new_context(storage_state=self.user.context)

    def get_playwright(self) -> PlaywrightContextManager:
        return sync_playwright()

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

            print(groups_links)
            groups = []
            for link in groups_links.all():
                if link.text_content():
                    groups.append(dict(
                        url=link.get_attribute('href'),
                        name=link.text_content()
                    ))
            page.close()
            return groups

    def create_post(self, group: FacebookGroup, post: FacebookPost):
        group.refresh_from_db()
        post.refresh_from_db()
        with self.get_playwright() as pw:
            try:
                page = self.get_browser(pw).new_page()
                page.goto(group.url, timeout=settings.PLAYWRIGHT['timeout'])
                page.get_by_text('Escribe algo…').click()
                page.click('[aria-placeholder="Crea una publicación pública..."]')

                file_input = page.locator('input[type="file"][multiple]')
                file_input.set_input_files(files=[post.file.path])
                page.keyboard.type(post.text)

                page.click('[aria-label="Publicar"]')
                page.get_by_text("Publicando", exact=True).wait_for(state='hidden',
                                                                    timeout=settings.PLAYWRIGHT['timeout'])
                page.close()
            except Exception as e:
                file_name = f"{group}_screenshot.jpeg"
                image_bytes = page.screenshot(full_page=True, quality=80, type='jpeg')
                # group.screenshot.save(file_name, ContentFile(image_bytes))
                sync_to_async(group.screenshot.save)(file_name, ContentFile(image_bytes), True)
                group.asave()
