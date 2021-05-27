import cachetools


def autotuple_hashkey(*args, **kwargs):
    """Convert lists in args or kwargs to tuple, then pass to `cachetools.keys.hashkey`.

    Useful for function that accept lists at arguments. Converting them to a tuple makes
    them cacheable and hence usable in `cachetools`.

    This function is non-recursive, i.e., it does not work for nested lists.
    It works for an argument like [1, 2, 3], but not for [1, 2, [1, 2, 3]].
    """
    args = [tuple(arg) if isinstance(arg, list) else arg for arg in args]
    kwargs = {k: tuple(v) if isinstance(v, list) else v for k, v in kwargs.items()}
    return cachetools.keys.hashkey(*args, **kwargs)
