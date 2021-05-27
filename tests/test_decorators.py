import pytest
from cachetools import LRUCache

from shelved_cache.decorators import cachedasyncmethod


@pytest.mark.asyncio
async def test_cachedasyncmethod_async():
    class A:
        @cachedasyncmethod(lambda self: LRUCache(2))
        async def asum(self, a, b):
            return a + b

    a = A()
    assert await a.asum(1, 2) == 3


@pytest.mark.asyncio
async def test_cachedasyncmethod_sync():
    class A:
        @cachedasyncmethod(lambda self: LRUCache(2))
        def sum(self, a, b):
            return a + b

    a = A()
    assert a.sum(1, 2) == 3
