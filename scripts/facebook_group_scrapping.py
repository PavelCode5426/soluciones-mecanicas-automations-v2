import time
import re

from playwright.sync_api import sync_playwright, ElementHandle


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


state_file = "states/facebook.json"
timeout = 60 * 100000
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False, slow_mo=500, timeout=timeout).new_context(
        storage_state=str(state_file))

    page = browser.new_page()
    group_url = 'https://www.facebook.com/groups/132729046531396/'
    page.goto(group_url, timeout=timeout)

    last_height = page.evaluate("document.body.scrollHeight")

    facebook_articles = []
    attemps = 1

    feed = page.get_by_role('feed')
    for attemp in range(attemps):
        page.evaluate(f"window.scrollBy(0,document.body.scrollHeight)")
        time.sleep(3)
        facebook_articles.extend(page.query_selector_all('div[aria-posinset]'))

    for article in facebook_articles:
        post = FacebookPostExtractor(article).extract_all()
        print(post)

    input("Salir...")
