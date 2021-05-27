# shelved_cache

Persistent Cache implementation for Python cachetools.

Original repository: [https://github.com/mariushelf/shelved_cache](https://github.com/mariushelf/shelved_cache)

# Usage example

```python
from shelved_cache import PersistentCache
from cachetools import LRUCache

filename = 'mycache'

# create persistency around an LRUCache
pc = PersistentCache(LRUCache, filename=filename, maxsize=2)

# we can now use the cache like a normal LRUCache:
pc["a"] = 42
pc["b"] = 43

assert pc["a"] == 42
assert pc["b"] == 43

pc["c"] = 44
# "a" should be evicted now because maxsize is 2

assert "a" not in pc

# close the file
pc.close()

# Now in the same script or in another script, we can re-load the cache:
pc2 = PersistentCache(LRUCache, filename=filename, maxsize=2)
assert pc2["b"] == 43
assert pc2["c"] == 44
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

# License

Author: Marius Helf ([helfsmarius@gmail.com](mailto:helfsmarius@gmail.com))

License: MIT -- see [LICENSE](LICENSE)
