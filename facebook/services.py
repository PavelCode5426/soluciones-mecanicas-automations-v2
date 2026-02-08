import random
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

    def check_status(self):
        self.refresh_user()
        if self.user.active:
            with (get_playwright() as pw):
                browser = self.get_browser(pw)
                page = browser.new_page()
                page.goto('https://www.facebook.com/')
                self.user.active = not bool(page.locator('text=Iniciar sesión').count())
        self.user.save(update_fields=['active'])
        return self.user.active

    def refresh_user(self):
        self.user.refresh_from_db()

    def get_browser(self, pw: Playwright):
        context = pw.chromium.launch(**settings.PLAYWRIGHT).new_context(storage_state=self.user.context)
        context.set_default_timeout(settings.PLAYWRIGHT['timeout'])
        return context

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
        if post.active and group.active and self.user.active:
            screenshot, exception = self.__publish_group_post(group.url, post)
            file_name = f"{group}_screenshot.jpeg".lower()
            group.screenshot.delete(False)
            group.screenshot.save(file_name, ContentFile(screenshot), False)

            group.error_at = None
            if exception:
                group.error_at = now()
                group.save()
                raise exception

            group.save()
            post.published_count = F('published_count') + 1
            post.save()

    def __publish_group_post(self, url, post: FacebookPost) -> (bytes, Exception | None):
        exception = None
        with (get_playwright() as pw):
            try:
                browser = self.get_browser(pw)
                page = browser.new_page()
                page.goto(url)

                # page.get_by_text('Escribe algo').click(timeout=settings.PLAYWRIGHT['timeout'])
                # page.get_by_role('textbox').click(timeout=settings.PLAYWRIGHT['timeout'])
                # file_input = page.locator('input[type="file"][multiple]')
                # file_input.set_input_files(files=[post.file.path])
                # page.keyboard.type(post.text)
                # page.get_by_text('Publicar').click()
                # page.get_by_text("Publicando").wait_for(state='hidden')

                page.wait_for_load_state(state='load')
                write_btn = page.get_by_text('Escribe algo')
                write_btn.wait_for(state='visible')
                write_btn.click()

                # page.get_by_text('Crear publicación').wait_for(state='visible')
                text_area = page.locator('[aria-placeholder*="Crea una publicación"]')
                # text_area.wait_for(state='visible')
                text_area.click()

                file_input = page.locator('input[type="file"][multiple]')
                file_input.set_input_files(files=[post.file.path])

                # page.keyboard.type(post.text)
                page.keyboard.insert_text(post.text)
                time.sleep(random.randint(30, 60))

                page.click('[aria-label="Publicar"]')
                page.get_by_text("Publicando", exact=True).wait_for(state='hidden')

            except Exception as e:
                exception = e
            return page.screenshot(quality=80, type='jpeg'), exception

    def sign_in(self, user: FacebookProfile):
        pass
