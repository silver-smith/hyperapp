from .tested.services import (
    fn_to_ref,
    )


def _test_fn():
    pass


def test_fn_to_ref():
    return fn_to_ref(_test_fn)
