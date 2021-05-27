# shelved_cache

Persistent Cache implementation for Python cachetools.

Behaves like any `Cache` implementation, but entries are persisted to disk.

Original repository: [https://github.com/mariushelf/shelved_cache](https://github.com/mariushelf/shelved_cache)

# Usage example

```python
from shelved_cache import PersistentCache
from cachetools import LRUCache

filename = 'mycache'

# create persistency around an LRUCache
pc = PersistentCache(LRUCache, filename=filename, maxsize=2)

# we can now use the cache like a normal LRUCache.
# But: the cache is persisted to disk.
pc["a"] = 42
pc["b"] = 43

assert pc["a"] == 42
assert pc["b"] == 43

# close the file
pc.close()

# Now in the same script or in another script, we can re-load the cache:
pc2 = PersistentCache(LRUCache, filename=filename, maxsize=2)
assert pc2["a"] == 42
assert pc2["b"] == 43
```

## Use as a decorator

Just like a regular `cachetools.Cache`, the `PersistentCache` can be used with
`cachetools`' `cached` decorator:

```python
from shelved_cache import PersistentCache
from cachetools import LRUCache

filename = 'mycache'
pc = PersistentCache(LRUCache, filename, maxsize=2)

@cachetools.cached(pc)
def square(x):
    print("called")
    return x * x

assert square(3) == 9
# outputs "called"
assert square(3) == 9
# no output because the cache is used
```


# Features

## persistent cache

See usage examples above.

## Async decorators

The package contains equivalents for `cachetools`' `cached` and `cachedmethod`
decorators which support wrapping async methods. You can find them in the `decorators`
submodule.

They support both synchronous *and* asynchronous functions and methods.

Examples:
```python
from shelved_cache import cachedasyncmethod
from cachetools import LRUCache

class A:
    # decorate an async method:
    @cachedasyncmethod(lambda self: LRUCache(2))
    async def asum(self, a, b):
        return a + b

a = A()
assert await a.asum(1, 2) == 3
    
class S:
    @cachedasyncmethod(lambda self: LRUCache(2))
    def sum(self, a, b):
        return a + b

s = S()
assert s.sum(1, 2) == 3
```


## Support for lists as function arguments

Using the `autotuple_hashkey` function, list arguments are automatically converted
to tuples, so that they support hashing.

Example:
```python
from cachetools import cached, LRUCache
from shelved_cache.keys import autotuple_hashkey

@cached(LRUCache(2), key=autotuple_hashkey)
def sum(values):
    return values[0] + values[1]

# fill cache
assert sum([1, 2]) == 3

# access cache
assert sum([1, 2]) == 3
```

# License

Author: Marius Helf ([helfsmarius@gmail.com](mailto:helfsmarius@gmail.com))

License: MIT -- see [LICENSE](LICENSE)
