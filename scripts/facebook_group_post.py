import time
from pathlib import Path

from playwright.sync_api import sync_playwright

state_file = Path(__file__).parent.joinpath("states/facebook_pizzas_time.json")

url = "https://www.facebook.com/share/g/18UgnJk2ps/"

post_title = "🏪 VENTAS AL POR MAYOR – FEROS GRUPO"

post_text = """Somos una MIPYME dedicada principalmente a la distribución de pollo, nuestro producto estrella, además de otros alimentos básicos para tu cocina o punto de venta. Ofrecemos distintas presentaciones de pollo según disponibilidad, para que siempre encuentres la opción que mejor se ajuste a tus necesidades.

🍗 Pollo fresco a granel – práctico y económico.
🥫 Conservas y salsas Vima – tomate, mayonesa, ajo, leche evaporada y más.
🐟 Atún Atlántiko – gran sabor y excelente rendimiento.
🧀 Queso Gouda – perfecto para pizzas, bocadillos y recetas gourmet.
🥛 Leche en polvo – rendimiento asegurado para tu negocio.
🍺 Cerveza Sagres – calidad europea a precio mayorista.

✅ Precios realmente competitivos.
✅ Atención personalizada de lunes a sábado.
✅ Compra sencilla y rápida a través de WhatsApp."""

post_hastag = """"""
post_footer = """📦 Todas las reservas deben buscarse el mismo día. Si no va el cliente, pierde su reserva.

🚨🚨 Contamos con servicio de transportación. Mínima compra 20 cajas. 🚨🚨
🚨 Los pedidos se hacen previas reservas. Contacto para las reservas:  
📞 58462015 / 52066528 / 53491811 🚨

👉 https://chat.whatsapp.com/FJXetpvAYsu3Uue3VrgnSd

📲 Únete a nuestro grupo de WhatsApp para recibir información y ofertas a diario."""
post_files = list(Path(__file__).parent.joinpath("data").glob('*'))

timeout = 60 * 100000
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False, slow_mo=1500, timeout=timeout).new_context(
        storage_state=str(state_file),
        # viewport={"width": 390, "height": 644},
        # record_video_dir="videos/", record_video_size={"width": 390, "height": 644}
    )
    # browser = pw.chromium.launch(headless=False, slow_mo=500, timeout=timeout).new_context(storage_state=state_file)

    page = browser.new_page()
    page.goto(url, wait_until='load', timeout=timeout)
    write_btn = page.get_by_text('Escribe algo')
    write_btn.wait_for(state='visible')
    write_btn.click()

    attempts = 3
    dialog = page.get_by_role('dialog').first
    while attempts > 0:
        if dialog.is_visible():
            break
        write_btn.click()
        attempts -= 1
    # dialog.wait_for(state='visible')

    publicar_btn = dialog.locator('[aria-label="Publicar"]')
    publicar_btn.wait_for(state='visible')

    if len(post_files):
        file_input = page.locator('input[type="file"][multiple]').first
        file_input.set_input_files(files=post_files)

    page.keyboard.type(post_title)
    page.keyboard.press('Enter')
    page.keyboard.type(post_text)
    page.keyboard.press('Enter')
    page.keyboard.press('Enter')
    page.keyboard.type(post_footer)

    hashtags = post_hastag.strip()
    if hashtags:
        page.keyboard.press('Enter')
        page.keyboard.press('Enter')
        for hastag in hashtags.split("\n"):
            page.keyboard.type(hastag.strip())
            page.keyboard.press('Enter')
            page.keyboard.press("Space")

    time.sleep(3)
    publicar_btn.click()
    page.locator('span', has_text='Publicando').wait_for(state='hidden')
    input("")
