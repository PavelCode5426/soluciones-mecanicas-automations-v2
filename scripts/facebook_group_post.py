import time
from pathlib import Path

from playwright.sync_api import sync_playwright

state_file = Path(__file__).parent.joinpath("states/facebook.json")

url = "https://www.facebook.com/groups/ventasencuba/"

post_title = "Neveras en venta"

post_text = """
❄️ ¡Elige la nevera Milexus perfecta para tu espacio! ❄️

Tamaños disponibles:
11.2 pies → 💲360 USD
8.8 pies → 💲295 USD
7.0 pies → 💲240 USD
6.0 pies → 💲220 USD
4.2 pies → 💲180 USD

✅ Diseño moderno y compacto
✅ Excelente capacidad de almacenamiento
✅ Eficiencia energética y refrigerante ecológico
✅ Ideales para hogares, cafeterías y pequeños negocios

📩 Escríbeme para más detalles o reservar la tuya.
"""

post_hastag = """
#NeverasMilexus
#Refrigeradores
#EficienciaEnergética
#NeverasPremium
#CompraInteligente
"""
post_footer = """
ELECTRODOMÉSTICOS HABANA 🏠✨
¡Equipa tu hogar o impulsa tu negocio con la mejor calidad!
✅ Venta de electrodomésticos de todo tipo.
💰 Precios especiales exclusivos para compras al por mayor.
🚚 Envíos disponibles a toda La Habana y zonas aledañas (con costo adicional).
📍 Visítanos: Almacén ubicado en Guanabacoa.
📲 ¿Dudas o pedidos? Escríbenos directamente por WhatsApp: +53 53454688


🚀✨ Publicación generada por Sinergia Marketing Automations – Vende más, trabaja menos 💼📈

¿Cansado de perder tiempo respondiendo mensajes y organizando ventas manualmente? 😓📲
👉 Haz que tu marketing trabaje solo mientras tú te concentras en crecer.
📲 Contáctanos al +53 50735591 y convierte tu negocio en una máquina de ventas automatizada.
"""
post_file = Path(__file__).parent.joinpath("data/NEVERAS_MILEXUS_2.jpg")

timeout = 60 * 100000
with sync_playwright() as pw:
    device = pw.devices['iPhone 12']
    browser = pw.chromium.launch(headless=False, slow_mo=1500, timeout=timeout).new_context(
        storage_state=str(state_file),
        viewport={"width": 390, "height": 644},
        record_video_dir="videos/", record_video_size={"width": 390, "height": 644})
    # browser = pw.chromium.launch(headless=False, slow_mo=500, timeout=timeout).new_context(storage_state=state_file)

    page = browser.new_page()
    page.goto(url, wait_until='networkidle', timeout=timeout)
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

    if post_file:
        file_input = page.locator('input[type="file"][multiple]')
        file_input.set_input_files(files=[post_file])

    page.keyboard.type(post_title)
    page.keyboard.press('Enter')
    page.keyboard.type(post_text)
    page.keyboard.press('Enter')
    page.keyboard.press('Enter')
    page.keyboard.type(post_footer)
    page.keyboard.press('Enter')
    page.keyboard.press('Enter')

    hashtags = post_hastag.split("\n")
    for hastag in hashtags:
        page.keyboard.type(hastag.strip())
        page.keyboard.press('Enter')
        page.keyboard.press("Space")

    time.sleep(3)
    publicar_btn.click()
    page.locator('span', has_text='Publicando').wait_for(state='hidden')
    input("")
