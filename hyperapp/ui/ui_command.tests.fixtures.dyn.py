# from . import htypes
from .services import (
    association_reg,
    fn_to_res,
    pyobj_creg,
    mark,
    )


def _sample_fn():
    pass


class PhonyAssociationRegistry:

    def __getitem__(self, key):
        return fn_to_res(_sample_fn)


@mark.service
def association_reg():
    return PhonyAssociationRegistry()
