import asyncio
import concurrent.futures
from functools import wraps

_thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)


def run_async(coro):
    """
    Execute an async coroutine in a new event loop within a thread pool.
    Properly handles cleanup of the event loop to avoid resource leaks.

    Usage:
        async def my_async_func():
            await something()
            return result

        result = run_async(my_async_func())
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
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
