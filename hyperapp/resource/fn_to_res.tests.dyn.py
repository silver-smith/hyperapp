from .services import (
    mark,
    )
from .tested.code import fn_to_res
from .tested.services import fn_to_ref


class _PhonyPyObjCReg:
    def reverse_resolve(self, obj):
        return 'some object'


@mark.service
def pyobj_creg():
    return _PhonyPyObjCReg()


def _test_fn():
    pass


def test_fn_to_ref():
    return fn_to_ref(_test_fn)
