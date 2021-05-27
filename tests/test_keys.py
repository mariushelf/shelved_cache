from cachetools import LRUCache, cached
from cachetools.keys import hashkey

from shelved_cache.keys import autotuple_hashkey


def test_autotuple_hashkey_args():
    result = autotuple_hashkey(1, 2, [1, 2, 3])
    expected = (1, 2, (1, 2, 3))

    assert result == expected


def test_autotuple_haskey_kwargs():
    result = autotuple_hashkey(a=1, b=2, c=[1, 2, 3])
    expected = hashkey(a=1, b=2, c=(1, 2, 3))

    assert result == expected


def test_in_decorator():
    @cached(LRUCache(2), key=autotuple_hashkey)
    def sum(values):
        return values[0] + values[1]

    # fill cache
    assert sum([1, 2]) == 3

    # access cache
    assert sum([1, 2]) == 3
