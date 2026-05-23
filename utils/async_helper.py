import asyncio
import concurrent.futures

from utils.constants import THREAD_POOL_SIZE
from utils.logger import setup_logger

logger = setup_logger("AsyncHelper")
_thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=THREAD_POOL_SIZE)


def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    logger.debug("Running async coroutine")
    try:
        result = loop.run_until_complete(coro)
        logger.debug("Async coroutine completed")
        return result
    except Exception as e:
        logger.error(f"Async coroutine failed: {e}", exc_info=True)
        raise
    finally:
        loop.close()


def run_async_in_thread(coro):
    """
    Submit an async coroutine to run in a background thread.
    Returns a Future that can be used to get the result or exceptions.

    Usage:
        future = run_async_in_thread(some_async_func())
        # Later:
        try:
            result = future.result(timeout=30)
        except Exception as e:
            handle_error(e)
    """

    def _run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    return _thread_pool.submit(_run)
