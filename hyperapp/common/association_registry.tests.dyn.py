from . import htypes
from .services import (
    meta_registry,
    )
from .tested.services import association_reg


def do_nothing():
    pass


def test_register():
    ass_t = htypes.association_registry_tests.test_association
    meta_registry.register_actor(ass_t, do_nothing)
    ass_list = [ass_t()]
    association_reg.register_association_list(ass_list)
