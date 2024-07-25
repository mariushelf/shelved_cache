"""
Helpers to use [cachetools](https://github.com/tkem/cachetools) with
asyncio.

Some functions are copied from [asyncache](https://github.com/hephex/asyncache)
under the MIT license:


MIT License

Copyright (c) 2018 hephex

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import functools
import inspect
from typing import MutableMapping, ContextManager, Callable, Optional, AsyncContextManager

from cachetools import keys

__all__ = ["persistent_cached", "persistent_cachedmethod", "asynccached", "cachedasyncmethod"]


class nullcontext:
    """A class for noop context managers."""

    def __enter__(self):
        """Return ``self`` upon entering the runtime context."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Raise any exception triggered within the runtime context."""
        return None

    async def __aenter__(self):
        """Return ``self`` upon entering the runtime context."""
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Raise any exception triggered within the runtime context."""
        return None


def persistent_cached(cache: MutableMapping, key: Callable = keys.hashkey, lock: ContextManager = None):
    lock = lock or nullcontext()

    def decorator(func):
        def wrapper(*args, **kwargs):
            k = key(*args, **kwargs, __pc_function__name=func.__qualname__)
            try:
                with lock:
                    return cache[k]

            except KeyError:
                pass  # key not found

            val = func(*args, **kwargs)

            try:
                with lock:
                    cache[k] = val

            except ValueError:
                pass  # val too large

            return val

        return functools.wraps(func)(wrapper)

    return decorator


def persistent_cachedmethod(cache: Callable[[object], Optional[MutableMapping]], key: Callable = keys.methodkey,
                            lock: ContextManager = None):
    lock = lock or (lambda self: nullcontext())

    def decorator(method):
        def wrapper(self, *args, **kwargs):
            c = cache(self)
            if c is None:
                return method(self, *args, **kwargs)
            k = key(self, *args, **kwargs, __pc_function__name=method.__qualname__)
            try:
                with lock(self):
                    return c[k]

            except KeyError:
                pass  # key not found

            v = method(self, *args, **kwargs)

            try:
                with lock(self):
                    return c.setdefault(k, v)

            except ValueError:
                pass  # val too large

            return v

        return functools.update_wrapper(wrapper, method)

    return decorator


def asynccached(cache: MutableMapping, key=keys.hashkey, lock: AsyncContextManager | ContextManager = None):
    """
    Decorator to wrap a function or a coroutine with a memoizing callable
    that saves results in a cache.
    When ``lock`` is provided for a standard function, it's expected to
    implement ``__enter__`` and ``__exit__`` that will be used to lock
    the cache when gets updated. If it wraps a coroutine, ``lock``
    must implement ``__aenter__`` and ``__aexit__``.
    """
    lock = lock or nullcontext()

    def decorator(func):
        if inspect.iscoroutinefunction(func):

            async def wrapper(*args, **kwargs):
                k = key(*args, **kwargs, __pc_function__name=func.__qualname__)
                try:
                    async with lock:
                        return cache[k]

                except KeyError:
                    pass  # key not found

                val = await func(*args, **kwargs)

                try:
                    async with lock:
                        cache[k] = val

                except ValueError:
                    pass  # val too large

                return val

        else:

            def wrapper(*args, **kwargs):
                k = key(*args, **kwargs, __pc_function__name=func.__qualname__)
                try:
                    with lock:
                        return cache[k]

                except KeyError:
                    pass  # key not found

                val = func(*args, **kwargs)

                try:
                    with lock:
                        cache[k] = val

                except ValueError:
                    pass  # val too large

                return val

        return functools.wraps(func)(wrapper)

    return decorator


def cachedasyncmethod(cache: Callable[[object], Optional[MutableMapping]], key: Callable = keys.methodkey, lock: AsyncContextManager | ContextManager = None):
    """Decorator to wrap a class or instance method with a memoizing
    callable that saves results in a cache.

    """
    lock = lock or (lambda self: nullcontext())

    def decorator(method):
        if inspect.iscoroutinefunction(method):

            async def wrapper(self, *args, **kwargs):
                c = cache(self)
                if c is None:
                    return await method(self, *args, **kwargs)
                k = key(self, *args, **kwargs, __pc_function__name=method.__qualname__)
                try:
                    async with lock(self):
                        return c[k]
                except KeyError:
                    pass  # key not found
                v = await method(self, *args, **kwargs)
                # in case of a race, prefer the item already in the cache
                try:
                    async with lock(self):
                        return c.setdefault(k, v)
                except ValueError:
                    return v  # value too large

            return functools.update_wrapper(wrapper, method)
        else:
            decorator = persistent_cachedmethod(cache, key, lock)
            return decorator(method)

    return decorator
