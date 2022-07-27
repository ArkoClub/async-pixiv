from contextlib import contextmanager


@contextmanager
def no_warning() -> None:
    import warnings
    from copy import deepcopy
    filters = deepcopy(warnings.filters)
    try:
        warnings.filterwarnings("ignore")
        yield
    finally:
        warnings.resetwarnings()
        for f in filters:
            # noinspection PyUnresolvedReferences
            warnings.filters.append(filters)
