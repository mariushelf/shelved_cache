# shelved_cache

Persistent Cache for Python cachetools.

Original repository: [https://github.com/mariushelf/shelved_cache](https://github.com/mariushelf/shelved_cache)

# Usage example

```python
filename = 'mycache'
from shelved_cache import PersistentCache
from cachetools import LRUCache

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
```


# License

Author: Marius Helf ([helfsmarius@gmail.com](mailto:helfsmarius@gmail.com))

License: MIT -- see [LICENSE](LICENSE)
