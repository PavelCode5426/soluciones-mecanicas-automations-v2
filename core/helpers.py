import nest_asyncio
import asyncio


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


def run_async_safe(coro):
    """
    Ejecuta una corrutina de forma síncrona en entornos donde
    el event loop puede o no existir/estar corriendo.
    """
    try:
        # Intentamos obtener el loop actual
        loop = asyncio.get_event_loop()
    except Exception:
        # Si no hay loop en este hilo (común en Django-Q), creamos uno
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        # Si el loop ya está corriendo (ej. estamos en un entorno asíncrono)
        # nest_asyncio permite re-entrar al loop.
        nest_asyncio.apply()
        return loop.run_until_complete(coro)
    else:
        return loop.run_until_complete(coro)
