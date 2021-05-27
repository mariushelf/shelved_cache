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


def test_eviction(tmpdir):
    filename = os.path.join(tmpdir, "cache")
    pc = PersistentCache(LRUCache, filename=filename, maxsize=2)
    pc["a"] = 42
    pc["b"] = 43
    pc["c"] = 44
    # "a" should be evicted now
    assert "a" not in pc
    assert "a" not in pc.persistent_dict
    assert "b" in pc
    assert "b" in pc.persistent_dict


def test_persistency(tmpdir):
    filename = os.path.join(tmpdir, "cache")
    print(filename)
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
    assert "b" in pc2


def test_decorator(tmpdir):
    filename = os.path.join(tmpdir, "cache")
    pc = PersistentCache(LRUCache, filename, maxsize=2)

    @cachetools.cached(pc)
    def square(x):
        return x * x

    assert square(3) == 9
    assert 3 in pc
    assert 3 in pc.persistent_dict
