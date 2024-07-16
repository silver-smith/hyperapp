from .services import (
    mark,
    mosaic,
    )
from .tested.services import fn_to_ref


class _PhonyPyObjCReg:
    def actor_to_ref(self, obj):
        return mosaic.put('some object')


@mark.service
def pyobj_creg():
    return _PhonyPyObjCReg()


def _test_fn():
    pass


def test_fn_to_ref():
    return fn_to_ref(_test_fn)
