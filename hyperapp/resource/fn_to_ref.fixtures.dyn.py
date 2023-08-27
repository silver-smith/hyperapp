from .services import (
    mark,
    )


class _PhonyPyObjCReg:
    def reverse_resolve(self, obj):
        return 'some object'


@mark.service
def pyobj_creg():
    return _PhonyPyObjCReg()
