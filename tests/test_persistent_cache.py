import os
import tempfile
from asyncio import Lock

import pytest
from cachetools import LRUCache

from shelved_cache.decorators import persistent_cached, asynccached, cachedasyncmethod
from shelved_cache.persistent_cache import PersistentCache


@pytest.fixture
def tmpfile():
    with tempfile.NamedTemporaryFile() as f:
        yield f.name


@pytest.fixture
def tmpdir():
    with tempfile.TemporaryDirectory() as d:
        yield d


def test_getsetitem(tmpdir):
    filename = os.path.join(tmpdir, "cache")
    pc = PersistentCache(LRUCache, filename=filename, maxsize=3)
    pc["a"] = 42
    assert pc["a"] == 42


def test_setdefault(tmpdir):
    filename = os.path.join(tmpdir, "cache")
    pc = PersistentCache(LRUCache, filename=filename, maxsize=3)

    # insert
    res = pc.setdefault("a", 42)
    assert res == 42
    assert pc.persistent_dict[str(hash("a"))] == ("a", 42)

    # retrieve
    res = pc.setdefault("a", 42)
    assert res == 42
    assert pc.persistent_dict[str(hash("a"))] == ("a", 42)


def test_eviction(tmpdir):
    filename = os.path.join(tmpdir, "cache")
    pc = PersistentCache(LRUCache, filename=filename, maxsize=2)
    pc["a"] = 42
    pc["b"] = 43
    pc["c"] = 44
    # "a" should be evicted now
    assert "a" not in pc
    assert PersistentCache.hash_key("a") not in pc.persistent_dict
    assert "b" in pc
    assert PersistentCache.hash_key("b") in pc.persistent_dict


def test_non_string_keys(tmpdir):
    filename = os.path.join(tmpdir, "cache")
    pc = PersistentCache(LRUCache, filename=filename, maxsize=3)
    pc[23] = 42
    assert pc[23] == 42


def test_persistency(tmpdir):
    filename = os.path.join(tmpdir, "cache")
    pc = PersistentCache(LRUCache, filename=filename, maxsize=2)
    pc["a"] = 42
    pc["b"] = 43
    pc["c"] = 44
    # "a" should be evicted now
    assert "a" not in pc
    assert "b" in pc
    pc.close()

    pc2 = PersistentCache(LRUCache, filename=filename, maxsize=2)
    assert "a" not in pc2
    assert pc2["b"] == 43
    assert pc2["c"] == 44


def test_no_persistency():
    filename = None
    pc = PersistentCache(LRUCache, filename=filename, maxsize=2)
    pc["a"] = 42
    pc["b"] = 43
    pc["c"] = 44
    # "a" should be evicted now
    assert "a" not in pc
    assert "b" in pc
    pc.close()

    pc2 = PersistentCache(LRUCache, filename=filename, maxsize=2)
    assert "a" not in pc2
    assert "b" not in pc2


def test_non_str_key_persistency(tmpdir):
    filename = os.path.join(tmpdir, "cache")
    pc = PersistentCache(LRUCache, filename=filename, maxsize=2)
    pc[23] = 42
    pc[24] = 43
    pc.close()

    pc2 = PersistentCache(LRUCache, filename=filename, maxsize=2)
    assert pc2[23] == 42
    assert pc2[24] == 43


def test_decorator(tmpdir):
    filename = os.path.join(tmpdir, "cache")
    pc = PersistentCache(LRUCache, filename, maxsize=2)

    square_calls = 0
    cube_calls = 0

    @persistent_cached(pc)
    def square(x):
        nonlocal square_calls
        square_calls += 1
        return x * x

    @persistent_cached(pc)
    def cube(x):
        nonlocal cube_calls
        cube_calls += 1
        return x * x * x


    assert square(3) == 9
    assert square(3) == 9
    assert square_calls == 1

    assert cube(3) == 27
    assert cube(3) == 27
    assert cube_calls == 1

@pytest.mark.asyncio
async def test_async_decorator(tmpdir):
    filename = os.path.join(tmpdir, "cache")
    pc = PersistentCache(LRUCache, filename, maxsize=2)

    lock = Lock()
    square_calls = 0
    cube_calls = 0

    @asynccached(pc)
    async def square(x):
        nonlocal square_calls

        async with lock:
            square_calls += 1

        return x * x

    @asynccached(pc)
    async def cube(x):
        nonlocal cube_calls

        async with lock:
            cube_calls += 1

        return x * x * x


    assert await square(3) == 9
    assert await square(3) == 9
    assert square_calls == 1

    assert await cube(3) == 27
    assert await cube(3) == 27
    assert cube_calls == 1

@pytest.mark.asyncio
async def test_wrong_async_decorator(tmpdir):
    """
    Tests asynccached on a function that is not async
    """

    filename = os.path.join(tmpdir, "cache")
    pc = PersistentCache(LRUCache, filename, maxsize=2)

    square_calls = 0
    cube_calls = 0

    @asynccached(pc)
    def square(x):
        nonlocal square_calls
        square_calls += 1
        return x * x

    @asynccached(pc)
    def cube(x):
        nonlocal cube_calls
        cube_calls += 1
        return x * x * x


    assert square(3) == 9
    assert square(3) == 9
    assert square_calls == 1

    assert cube(3) == 27
    assert cube(3) == 27
    assert cube_calls == 1


@pytest.mark.asyncio
async def test_asyncmethod_decorator(tmpdir):
    filename = os.path.join(tmpdir, "cache")
    pc = PersistentCache(LRUCache, filename, maxsize=2)

    lock = Lock()
    square_calls = 0
    cube_calls = 0

    class MyClass:
        @cachedasyncmethod(lambda _: pc)
        async def square(self, x):
            nonlocal square_calls

            async with lock:
                square_calls += 1

            return x * x

        @cachedasyncmethod(lambda _: pc)
        async def cube(self, x):
            nonlocal cube_calls

            async with lock:
                cube_calls += 1

            return x * x * x

    my_object = MyClass()

    assert await my_object.square(3) == 9
    assert await my_object.square(3) == 9
    assert square_calls == 1

    assert await my_object.cube(3) == 27
    assert await my_object.cube(3) == 27
    assert cube_calls == 1

@pytest.mark.asyncio
async def test_wrong_asyncmethod_decorator(tmpdir):
    """
    Tests cachedasyncmethod on a method that is not async
    """

    filename = os.path.join(tmpdir, "cache")
    pc = PersistentCache(LRUCache, filename, maxsize=2)

    square_calls = 0
    cube_calls = 0

    class MyClass:
        @cachedasyncmethod(lambda _: pc)
        def square(self, x):
            nonlocal square_calls
            square_calls += 1
            return x * x

        lock = Lock()

        @cachedasyncmethod(lambda _: pc)
        def cube(self, x):
            nonlocal cube_calls
            cube_calls += 1
            return x * x * x

    my_object = MyClass()

    assert my_object.square(3) == 9
    assert my_object.square(3) == 9
    assert square_calls == 1

    assert my_object.cube(3) == 27
    assert my_object.cube(3) == 27
    assert cube_calls == 1