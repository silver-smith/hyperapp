from unittest.mock import Mock

from . import htypes
from .services import (
    pyobj_creg,
    )
from .tested.code import column_resource_name


def test_resource_name():
    gen = Mock()
    piece = htypes.column.column_k(
        model_t=pyobj_creg.actor_to_ref(htypes.column_resource_name_tests.sample_model),
        column_name='sample_column',
        )
    name = column_resource_name.column_k_resource_name(piece, gen)
    assert name
