import os
import tempfile

import cachetools
import pytest
from cachetools import LRUCache

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

    @cachetools.cached(pc)
    def square(x):
        print("called")
        return x * x

    assert square(3) == 9
    # outputs "called"
    assert square(3) == 9
    # no output because the cache is used


@pytest.mark.xfail(reason="Use a new instance of PersistentCache for every function")
def test_two_function_same_cache(tmpdir):
    filename = os.path.join(tmpdir, "cache")
    pc = PersistentCache(LRUCache, filename, maxsize=1000)

    @cachetools.cached(pc)  # bad, do not do this. Use a new instance for every function
    def square(x):
        return x * x

    @cachetools.cached(pc)  # bad, do not do this. Use a new instance for every function
    def cube(x):
        return x * x * x

    assert square(2) == 4
    assert cube(2) == 8, "if this is 4, cube() uses the same cache as square()"
