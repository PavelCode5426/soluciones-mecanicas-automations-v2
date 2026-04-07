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
    """Ejecuta una corrutina de forma síncrona, funcionando tanto si hay un bucle corriendo como si no."""
    try:
        loop = asyncio.get_running_loop()
    except Exception:
        return asyncio.run(coro)
    else:
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result()
