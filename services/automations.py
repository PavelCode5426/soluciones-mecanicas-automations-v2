import asyncio
import random
import re
import time

import nest_asyncio
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import F
from django.utils.timezone import now
from playwright.sync_api import sync_playwright, PlaywrightContextManager, Playwright

from facebook.models import FacebookPost, FacebookLeadExplorer
from facebook.models import FacebookProfile, FacebookGroup
from ia_assistant.agents.workflows import FacebookPostAnalyzerAgent


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


class FacebookPostExtractor:
    """
    Extractor de datos de una publicación de Facebook usando Beautiful Soup.
    Recibe un objeto Tag de BeautifulSoup que representa un post individual.
    NOTA: No puede hacer clic en 'Ver más', por lo que el mensaje puede estar truncado.
    """

    def __init__(self, post_html):
        self.post = BeautifulSoup(post_html, "html.parser")

    def extract_author(self) -> dict:
        """
        Extrae nombre, URL del perfil y URL del avatar del autor.
        """
        author = {"name": None, "profile_url": None, "avatar_url": None}

        # Buscar contenedor del nombre (data-ad-rendering-role="profile_name")
        profile_container = self.post.find('div', attrs={'data-ad-rendering-role': 'profile_name'})
        if profile_container:
            link = profile_container.find('a')
            if link:
                author["name"] = link.get_text(strip=True)
                author["profile_url"] = link.get('href')

        # Avatar: buscar dentro del primer <svg> <image>
        svg_image = self.post.find('svg').find('image') if self.post.find('svg') else None
        if svg_image:
            author["avatar_url"] = svg_image.get('xlink:href')

        return author

    def extract_timestamp(self) -> str:
        """
        Extrae el texto de timestamp relativo buscando spans con patrones de tiempo.
        """
        # Buscar spans que contengan dígitos seguido de espacio y min/h/d/s...
        # Nota: Beautiful Soup no soporta :has-text, así que recorremos todos los spans
        for span in self.post.find_all('span'):
            text = span.get_text(strip=True)
            if re.search(r'\d+\s*(min|h|d|s|min\.|h\.)', text):
                return text

    def extract_message(self) -> str:
        message_div = self.post.find('div', attrs={'data-ad-rendering-role': 'story_message'})
        if not message_div:
            return ""
        return message_div.get_text(separator='\n', strip=True)

        # message_container = self.post.find('div', attrs={'data-ad-rendering-role': 'story_message'})
        # if message_container:
        #     # Extraer todas las líneas con dir="auto"
        #     lines = message_container.find_all('div', attrs={'dir': 'auto'})
        #     full_text = "\n".join([line.get_text(strip=True) for line in lines])
        #     return full_text

    def extract_images(self) -> list:
        """
        Devuelve lista de URLs de imágenes de la publicación (excluye avatar).
        """
        image_urls = []
        # Buscar imágenes cuyo src contenga "scontent" (dominio de CDN de FB)
        images = self.post.find_all('img', src=re.compile(r'scontent'))
        for img in images:
            src = img.get('src')
            # Excluir avatares (por tamaño pequeño) y duplicados
            if src and 's40x40' not in src and src not in image_urls:
                image_urls.append(src)
        return image_urls

    def extract_reactions(self) -> int:
        """
        Intenta obtener el número de reacciones buscando en aria-label o texto cercano.
        """
        # Buscar elemento con aria-label que contenga "Me gusta" y extraer números
        reaction_elem = self.post.find(attrs={'aria-label': re.compile(r'Me gusta')})
        if reaction_elem:
            label = reaction_elem.get('aria-label', '')
            numbers = re.findall(r'\d+', label)
            if numbers:
                return int(numbers[0])

        # Alternativa: buscar botón de like y luego en el padre
        like_button = self.post.find('div', attrs={'aria-label': 'Me gusta'})
        if like_button and like_button.parent:
            text = like_button.parent.get_text(strip=True)
            numbers = re.findall(r'\d+', text)
            if numbers:
                return int(numbers[0])

    def extract_comments_count(self) -> int:
        """
        Intenta obtener el número de comentarios.
        """
        comment_button = self.post.find('div', attrs={'aria-label': 'Dejar un comentario'})
        if comment_button and comment_button.parent:
            text = comment_button.parent.get_text(strip=True)
            numbers = re.findall(r'\d+', text)
            if numbers:
                return int(numbers[0])

    def extract_shares_count(self) -> int:
        """
        Intenta obtener el número de veces compartido.
        """
        share_button = self.post.find('div', attrs={'aria-label': re.compile(r'Envía la publicación')})
        if share_button and share_button.parent:
            text = share_button.parent.get_text(strip=True)
            numbers = re.findall(r'\d+', text)
            if numbers:
                return int(numbers[0])

    def extract_all(self) -> dict:
        """
        Ejecuta todas las extracciones y devuelve un diccionario completo.
        """
        return {
            "author": self.extract_author(),
            # "timestamp": self.extract_timestamp(),
            "message": self.extract_message(),
            # "images": self.extract_images(),
            # "reactions": self.extract_reactions(),
            # "comments": self.extract_comments_count(),
            # "shares": self.extract_shares_count(),
        }


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

    def create_post(self, group: FacebookGroup, post: FacebookPost):
        self.refresh_profile()
        group.refresh_from_db()
        post.refresh_from_db()
        if post.active and group.active and self.profile.active:
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
            post.save(update_fields=['published_count', 'updated_at'])

    def __publish_group_post(self, url, post: FacebookPost) -> (bytes, Exception | None):
        exception = None

        with (get_playwright() as pw):
            try:
                browser = self.get_browser(pw)
                page = browser.new_page()
                page.goto(url, wait_until='load')

                # page.get_by_text('Escribe algo').click(timeout=settings.PLAYWRIGHT['timeout'])
                # page.get_by_role('textbox').click(timeout=settings.PLAYWRIGHT['timeout'])
                # file_input = page.locator('input[type="file"][multiple]')
                # file_input.set_input_files(files=[post.file.path])
                # page.keyboard.type(post.text)
                # page.get_by_text('Publicar').click()
                # page.get_by_text("Publicando").wait_for(state='hidden')
                write_btn = page.get_by_text('Escribe algo')
                write_btn.wait_for(state='visible')
                write_btn.click()

                attempts = 3
                dialog = page.get_by_role('dialog')
                while attempts > 0:
                    if dialog.is_visible():
                        break
                    time.sleep(5)
                    write_btn.click()
                    attempts -= 1
                # dialog.wait_for(state='visible')

                publicar_btn = dialog.locator('[aria-label="Publicar"]')
                publicar_btn.wait_for(state='visible')
                time.sleep(10)

                # page.keyboard.type(post.title)
                page.keyboard.press('Enter')
                page.keyboard.insert_text(post.text)
                page.keyboard.press('Enter')
                page.keyboard.press('Enter')
                page.keyboard.insert_text(self.profile.posts_footer)
                page.keyboard.press('Enter')
                page.keyboard.press('Enter')

                hashtags = post.hashtags.split("\n")
                for hastag in hashtags:
                    page.keyboard.type(hastag.strip(), delay=600)
                    page.keyboard.press('Enter')
                    page.keyboard.press("Space")

                if post.file:
                    file_input = page.locator('input[type="file"][multiple]')
                    file_input.set_input_files(files=[post.file.path])

                time.sleep(random.randint(30, 60))
                publicar_btn.click()
                page.locator('span', has_text='Publicando').wait_for(state='hidden')
            except Exception as e:
                exception = e

            screenshot = page.screenshot(quality=80, type='jpeg')
            updated_session = browser.storage_state()

        self.save_session(updated_session)
        return screenshot, exception

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
                    page.goto(group.url, wait_until='commit')

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
                        post_analyser = FacebookPostAnalyzerAgent()
                        try:
                            response = run_async(post_analyser.run(raw_html=article.inner_html()))
                            if response.is_relevant:
                                textarea.click()
                                article.page.keyboard.type(response.promotional_message)
                                article.page.keyboard.press('Enter')
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
