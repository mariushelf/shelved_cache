import dbm
import logging
import os
import pickle
import shelve
from collections.abc import MutableMapping
from pathlib import Path
from shelve import Shelf
from typing import Any, Callable, Iterator, Type

from cachetools import Cache

logger = logging.getLogger(__name__)


class DelMixin:
    """Mixin that calls a callback after each call to the `__delitem__()` function."""

    def __init__(
        self, delete_callback: Callable[[str], Any], *args: Any, **kwargs: Any
    ) -> None:
        self.delete_callback = delete_callback
        super().__init__(*args, **kwargs)  # type: ignore

    def __delitem__(self, key):
        super().__delitem__(key)
        self.delete_callback(key)


class ShelvedCacheError(Exception):
    pass


class PersistentCache(MutableMapping):
    """Behaves like a subclass of `cachetools.Cache`, but keeps a persistent copy
    of the cache on disk.

    The persistent copy is lazily instantiated at the first access to an attribute
    of the underlying cache.

    The persistent copy is updated after every write (add or delete item).

    If items in the cache are modified without re-adding them to the dict, the
    persistent cache will not be updated.

    Persistency can be deactivated by providing `None` as the filename.

    Internally, the `shelve` library is used to implement the cache.

    Parameters
    ----------
    wrapped_cache_cls: subclass of `Cache`
        the class of the cache that this PersistentCache should mimic.
    filename: str or None
        filename for the persistent cache. A file extension may be appended. See
        `shelve.open()` for more information. If `None`, persistency is deactivated.
    *args:
        forwarded to the init function of `wrapped_cache_cls`
    *kwargs:
        forwarded to the init function of `wrapped_cache_cls`
    """

    def __init__(
        self, wrapped_cache_cls: Type[Cache], filename: str, *args, **kwargs
    ) -> None:
        new_cls = type(
            f"Wrapped{wrapped_cache_cls.__name__}", (DelMixin, wrapped_cache_cls), {}
        )
        if filename:
            self.wrapped = new_cls(self.delete_callback, *args, **kwargs)
        else:
            # no persistency, hence no callback needed
            self.wrapped = wrapped_cache_cls(*args, **kwargs)
        self.filename = filename
        self.persistent_dict: Shelf = None

    def delete_callback(self, key):
        """Called when an item is deleted from the wrapped cache"""
        self.initialize_if_not_initialized()
        hkey = self.hash_key(key)
        try:
            del self.persistent_dict[hkey]
        except KeyError:
            logger.warning(f"Key '{hkey}' not in persistent cache.")

    @staticmethod
    def hash_key(key):
        return str(hash(key))

    def __setitem__(self, key, value):
        self.initialize_if_not_initialized()
        hkey = self.hash_key(key)
        if self.persistent_dict is not None:
            self.persistent_dict[hkey] = (key, value)
            self.persistent_dict.sync()
        self.wrapped[key] = value

    def setdefault(self, k, v):
        try:
            return self.wrapped[k]
        except KeyError:
            self[k] = v
            return v

    def __getitem__(self, item):
        self.initialize_if_not_initialized()
        return self.wrapped[item]

    def __getattr__(self, item):
        self.initialize_if_not_initialized()
        return getattr(self.wrapped, item)

    def __delitem__(self, v) -> None:
        self.initialize_if_not_initialized()
        del self.persistent_dict[v]

    def __contains__(self, item):
        self.initialize_if_not_initialized()
        return self.wrapped.__contains__(item)

    def initialize_if_not_initialized(self):
        if self.filename and self.persistent_dict is None:
            # create cache directory if not exists
            dir = Path(self.filename).parent
            os.makedirs(dir, exist_ok=True)

            # load or create database file
            try:
                self.persistent_dict = shelve.open(
                    self.filename, protocol=pickle.HIGHEST_PROTOCOL, flag="c"
                )
                for hk, (k, v) in self.persistent_dict.items():
                    self.wrapped[k] = v
                logger.debug(
                    f"Loaded {len(self.persistent_dict)} cache entries from {self.filename} (in cache: {len(self.wrapped)})."
                )
            except pickle.UnpicklingError:
                # create a new cache file
                self._destroy_and_reinit_cache()
            except ValueError as e:
                # cache has been created with higher pickle protocol
                if "unsupported pickle protocol" in str(e):
                    self._destroy_and_reinit_cache()
            except dbm.error as e:
                # cache has been created with newer python version
                if "db type is dbm.gnu, but the module is not available" in str(e):
                    self._destroy_and_reinit_cache()
            except Exception as e:
                if "Resource temporarily unavailable" in str(e):
                    raise ShelvedCacheError(
                        "Resource temporarily unavailable. "
                        "Did you try to use the same file for multiple caches?"
                    )
                raise e

    def close(self):
        if self.persistent_dict is not None:
            self.persistent_dict.close()
            self.persistent_dict = None

    def __del__(self):
        """Try to tidy up.

        This is just for show since we sync the dict after every change anyway."""
        try:
            self.persistent_dict.close()
            self.persistent_dict = None
        except Exception:  # noqa: S110
            pass

    def __len__(self) -> int:
        self.initialize_if_not_initialized()
        return len(self.persistent_dict)

    def __iter__(self) -> Iterator:
        self.initialize_if_not_initialized()
        return iter(self.persistent_dict)

    def _destroy_and_reinit_cache(self):
        logger.warning(
            f"Failed to open cache database file {self.filename}. Overwriting with a new one."
        )
        self.persistent_dict = shelve.open(
            self.filename,
            protocol=pickle.HIGHEST_PROTOCOL,
            flag="n",
        )
        keys = self.wrapped.keys()
        for key in keys:
            del self.wrapped[key]
