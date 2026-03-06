import random
import re
import time

from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import F
from django.utils.timezone import now
from playwright.sync_api import sync_playwright, PlaywrightContextManager, Playwright, ElementHandle

from facebook.models import FacebookPost
from facebook.models import FacebookProfile, FacebookGroup


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

                if post.file:
                    file_input = page.locator('input[type="file"][multiple]')
                    file_input.set_input_files(files=[post.file.path])

                # page.keyboard.type(post.text)
                page.keyboard.insert_text(post.text)
                page.keyboard.insert_text('\n' * 2)
                page.keyboard.insert_text(self.user.posts_footer)
                time.sleep(random.randint(30, 60))

                page.click('[aria-label="Publicar"]')
                page.locator('span', has_text='Publicando').wait_for(state='hidden')
                # page.get_by_text("Publicando").wait_for(state='hidden')

            except Exception as e:
                exception = e
            return page.screenshot(quality=80, type='jpeg'), exception

    def sign_in(self, user: FacebookProfile):
        pass


class FacebookPostExtractor:
    """
    Extractor de datos de una publicación de Facebook usando Playwright.
    Recibe un ElementHandle que representa un post individual (con aria-posinset o role="article").
    """

    def __init__(self, post_element: ElementHandle):
        self.post = post_element

    def extract_author(self) -> dict:
        """
        Extrae nombre, URL del perfil y URL del avatar del autor.
        """
        author = {"name": None, "profile_url": None, "avatar_url": None}
        # Contenedor del nombre del autor
        profile_container = self.post.query_selector('div[data-ad-rendering-role="profile_name"]')
        if profile_container:
            link = profile_container.query_selector('a')
            if link:
                author["name"] = link.inner_text().strip()
                author["profile_url"] = link.get_attribute("href")
        # Avatar: buscar dentro del primer <svg> con máscara
        svg_image = self.post.query_selector('svg image')
        if svg_image:
            author["avatar_url"] = svg_image.get_attribute("xlink:href")
        return author

    def extract_timestamp(self) -> str:
        """
        Extrae el texto de timestamp relativo (ej. '8 min', '3 h').
        """
        # Buscar cualquier span que contenga patrones de tiempo (min, h, d, s)
        time_span = self.post.query_selector('span:has-text(/\\d+\\s*(min|h|d|s|min\\.|h\\.)/)')
        if time_span:
            return time_span.inner_text().strip()
        return None

    def extract_message(self) -> str:
        """
        Extrae el texto completo del mensaje, haciendo clic en 'Ver más' si existe.
        """
        message_container = self.post.query_selector('div[data-ad-rendering-role="story_message"]')
        if not message_container:
            return None

        # Intentar expandir si hay botón "Ver más"
        see_more = message_container.query_selector('div[role="button"]:has-text("Ver más")')
        if see_more:
            try:
                see_more.click()
                self.post.page.wait_for_timeout(500)  # Esperar a que se expanda
            except Exception:
                pass  # Si falla, continuamos con el texto actual

        # Extraer todas las líneas de texto (div con dir="auto")
        lines = message_container.query_selector_all('div[dir="auto"]')
        full_text = '\n'.join([line.inner_text().strip() for line in lines])
        return full_text

    def extract_images(self) -> list:
        """
        Devuelve lista de URLs de imágenes de la publicación (excluye avatar).
        """
        image_urls = []
        images = self.post.query_selector_all('img[src*="scontent"]')
        for img in images:
            src = img.get_attribute("src")
            # Excluir avatares (tamaño pequeño) y posibles duplicados
            if src and "s40x40" not in src and src not in image_urls:
                image_urls.append(src)
        return image_urls

    def extract_reactions(self) -> int:
        """
        Intenta obtener el número de reacciones (Me gusta).
        """
        # Buscar elemento con aria-label que contenga "Me gusta" y un número
        reaction_elem = self.post.query_selector('[aria-label*="Me gusta"]')
        if reaction_elem:
            label = reaction_elem.get_attribute("aria-label")
            numbers = re.findall(r'\d+', label)
            if numbers:
                return int(numbers[0])
        # Alternativa: buscar texto con números cerca del botón de like
        like_button = self.post.query_selector('div[aria-label="Me gusta"]')
        if like_button:
            parent = like_button.query_selector('xpath=..')
            if parent:
                text = parent.inner_text()
                numbers = re.findall(r'\d+', text)
                if numbers:
                    return int(numbers[0])
        return None

    def extract_comments_count(self) -> int:
        """
        Intenta obtener el número de comentarios.
        """
        comment_button = self.post.query_selector('div[aria-label="Dejar un comentario"]')
        if comment_button:
            parent = comment_button.query_selector('xpath=..')
            if parent:
                text = parent.inner_text()
                numbers = re.findall(r'\d+', text)
                if numbers:
                    return int(numbers[0])
        return None

    def extract_shares_count(self) -> int:
        """
        Intenta obtener el número de veces compartido.
        """
        share_button = self.post.query_selector('div[aria-label*="Envía la publicación"]')
        if share_button:
            parent = share_button.query_selector('xpath=..')
            if parent:
                text = parent.inner_text()
                numbers = re.findall(r'\d+', text)
                if numbers:
                    return int(numbers[0])
        return None

    def extract_all(self) -> dict:
        """
        Ejecuta todas las extracciones y devuelve un diccionario completo.
        """
        return {
            "author": self.extract_author(),
            "timestamp": self.extract_timestamp(),
            "message": self.extract_message(),
            "images": self.extract_images(),
            "reactions": self.extract_reactions(),
            "comments": self.extract_comments_count(),
            "shares": self.extract_shares_count(),
        }
