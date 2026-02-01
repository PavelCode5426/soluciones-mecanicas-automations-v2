import time

from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import F
from django.utils.timezone import now
from playwright.sync_api import sync_playwright, PlaywrightContextManager, Playwright

from facebook.models import FacebookProfile, FacebookPost, FacebookGroup


def get_playwright() -> PlaywrightContextManager:
    return sync_playwright()


class FacebookAutomationService:
    def __init__(self, user: FacebookProfile):
        self.user = user

    def refresh_user(self):
        self.user.refresh_from_db()

    def get_browser(self, pw: Playwright):
        return pw.chromium.launch(**settings.PLAYWRIGHT).new_context(storage_state=self.user.context)

    def get_all_groups(self):
        self.refresh_user()
        with get_playwright() as pw:
            browser = self.get_browser(pw)
            page = browser.new_page()
            page.goto("https://www.facebook.com/groups/joins/?nav_source=tab", timeout=settings.PLAYWRIGHT['timeout'])

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
            page.close()
            return groups

    def create_post(self, group: FacebookGroup, post: FacebookPost):
        self.refresh_user()
        group.refresh_from_db()
        post.refresh_from_db()
        if post.active and group.active:
            screenshot, exception = self.__publish_group_post(group.url, post)
            file_name = f"{group}_screenshot.jpeg".lower()
            group.screenshot.save(file_name, ContentFile(screenshot), False)

            group.error_at = None
            if exception:
                group.error_at = now()
                group.save()
                raise exception

            group.save()
            post.published_count = F('published_count') + 1
            post.save(update_fields=["published_count"])

    def __publish_group_post(self, url, post: FacebookPost) -> (bytes, Exception | None):
        exception = None
        with get_playwright() as pw:
            try:
                browser = self.get_browser(pw)
                page = browser.new_page()
                page.goto(url)
                page.get_by_text('Escribe algo…').click()
                page.click('[aria-placeholder="Crea una publicación pública..."]')

                file_input = page.locator('input[type="file"][multiple]')
                file_input.set_input_files(files=[post.file.path])
                page.keyboard.type(post.text)

                page.click('[aria-label="Publicar"]')
                page.get_by_text("Publicando", exact=True).wait_for(state='hidden')
            except Exception as e:
                exception = e
            return page.screenshot(full_page=True, quality=80, type='jpeg'), exception

    def sign_in(self, user: FacebookProfile):
        pass
