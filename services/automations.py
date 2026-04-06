import asyncio
import random
import time

import nest_asyncio
from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import F
from django.utils.timezone import now
from playwright.sync_api import sync_playwright, PlaywrightContextManager, Playwright
from workflows import Context

from facebook.models import FacebookPostCampaign, FacebookLeadExplorer, FacebookScheduledPost, AbstractFacebookPost
from facebook.models import FacebookProfile, FacebookGroup
from services.agents import FacebookPostAnalyzerAgent


def get_playwright() -> PlaywrightContextManager:
    return sync_playwright()


def run_async(coro):
    nest_asyncio.apply()
    new_loop = asyncio.get_event_loop()
    # new_loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(new_loop)
    try:
        return new_loop.run_until_complete(coro)
    finally:
        pass
        # new_loop.close()


class FacebookAutomationService:
    def __init__(self, profile: FacebookProfile):
        self.profile = profile

    def check_status(self):
        self.refresh_profile()
        if self.profile.active:
            with (get_playwright() as pw):
                browser = self.get_browser(pw)
                page = browser.new_page()
                page.goto('https://www.facebook.com/')
                active = not bool(page.locator('text=Iniciar sesión').count())
                self.profile.active = active
                if active:
                    dialog = page.get_by_role('dialog')
                    if dialog.is_visible():
                        close_btn = dialog.locator('[aria-label*="Cerrar"]')
                        close_btn.wait_for(state='visible')
                        close_btn.click()
                    storage_state = browser.storage_state()
                    self.profile.context = storage_state
        self.profile.save(update_fields=['active', 'context'])
        return self.profile.active

    def refresh_profile(self):
        self.profile.refresh_from_db()

    def get_browser(self, pw: Playwright):
        context = pw.chromium.launch(**settings.PLAYWRIGHT).new_context(storage_state=self.profile.context)
        context.set_default_timeout(settings.PLAYWRIGHT['timeout'])
        return context

    def get_all_groups(self):
        self.refresh_profile()
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

    def group_lead_explorer(self, explorer: FacebookLeadExplorer):
        self.refresh_profile()
        explorer.refresh_from_db()
        if explorer.active and self.profile.active:
            leads_found = 0
            group = explorer.group_category.groups.filter(active=True).order_by('?').first()
            with get_playwright() as pw:
                try:
                    browser = self.get_browser(pw)
                    page = browser.new_page()
                    page.goto("https://www.facebook.com/groups/feed/", wait_until='load')
                    post_analyser = FacebookPostAnalyzerAgent()
                    ctx = Context(post_analyser)

                    count = 0
                    while count <= 5:
                        articles_locator = page.locator("div[aria-posinset]")
                        count = articles_locator.count()
                        if count > 0:
                            page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                        time.sleep(5)

                    i = 0
                    while i < count and i < explorer.limit:
                        article = articles_locator.nth(i)
                        article.scroll_into_view_if_needed()
                        article.wait_for(state="visible")

                        try:
                            button = article.get_by_role("button", name="Ver más")
                            if button.is_visible(timeout=5):
                                button.click()
                        except Exception:
                            pass

                        textarea = article.get_by_role('textbox')
                        try:

                            response = run_async(post_analyser.run(raw_html=article.inner_html(), ctx=ctx))
                            if response.is_relevant:
                                textarea.click()
                                page.keyboard.type(response.promotional_message)
                                page.keyboard.press('Enter')
                                leads_found += 1

                        except Exception as e:
                            print(f"Lead explorer error: {e}")
                        count = articles_locator.count()
                        i += 1
                except Exception as e:
                    print(f"Lead explorer error: {e}")

            explorer.leads_found = F('leads_found') + leads_found
            explorer.save(update_fields=['leads_found'])

    def save_session(self, storage_state):
        self.profile.context = storage_state
        self.profile.save(update_fields=['context'])

    def publish_new_campaign(self, group: FacebookGroup, post: FacebookPostCampaign):
        self.refresh_profile()
        group.refresh_from_db()
        post.refresh_from_db()
        if post.active and group.active and self.profile.active:
            screenshot, exception = self.__publish_campaign(group.url, post)
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
            post.save(update_fields=['published_count', 'updated_at'])

    def publish_new_post(self, post: FacebookScheduledPost):
        self.refresh_profile()
        post.refresh_from_db()
        if post.active and self.profile.active:
            screenshot, exception = self.__publish_post(post)

    def __publish_campaign(self, group_url, post: FacebookPostCampaign) -> (bytes, Exception | None):
        exception = None

        with (get_playwright() as pw):
            try:
                browser = self.get_browser(pw)
                page = browser.new_page()

                page.goto(group_url, wait_until='load')
                open_dialog_button = page.get_by_text('Escribe algo')

                self.__write_post(page, open_dialog_button, post)
            except Exception as e:
                exception = e

            screenshot = page.screenshot(quality=80, type='jpeg')
            updated_session = browser.storage_state()

        self.save_session(updated_session)
        return screenshot, exception

    def __publish_post(self, post: FacebookScheduledPost) -> (bytes, Exception | None):
        exception = None

        with (get_playwright() as pw):
            try:
                browser = self.get_browser(pw)
                page = browser.new_page()

                page.goto('https://facebook.com', wait_until='load')
                open_dialog_button = page.get_by_text('¿Qué estás pensando')

                self.__write_post(page, open_dialog_button, post)
            except Exception as e:
                exception = e

            screenshot = page.screenshot(quality=80, type='jpeg')
            updated_session = browser.storage_state()

        self.save_session(updated_session)
        return screenshot, exception

    def __write_post(self, page, open_dialog_button, post: AbstractFacebookPost):
        open_dialog_button.wait_for(state='visible')
        open_dialog_button.click()

        attempts = 3
        dialog = page.get_by_role('dialog')
        while attempts > 0:
            if dialog.is_visible():
                break
            time.sleep(5)
            open_dialog_button.click()
            attempts -= 1

        publish_button = dialog.locator('[aria-label="Publicar"]')
        publish_button.wait_for(state='visible')
        time.sleep(10)

        page.keyboard.type(post.title)
        page.keyboard.press('Enter')
        page.keyboard.insert_text(post.text)
        page.keyboard.press('Enter')
        page.keyboard.press('Enter')
        page.keyboard.insert_text(self.profile.posts_footer)
        page.keyboard.press('Enter')
        page.keyboard.press('Enter')

        hashtags = post.hashtags.split("\n")
        for hastag in hashtags:
            page.keyboard.type(hastag.strip(), delay=300)
            page.keyboard.press('Enter')
            page.keyboard.press("Space")

        if post.file:
            file_input = page.locator('input[type="file"][multiple]')
            file_input.set_input_files(files=[post.file.path])

        time.sleep(random.randint(30, 60))
        publish_button.click()
        page.locator('span', has_text='Publicando').wait_for(state='hidden')
