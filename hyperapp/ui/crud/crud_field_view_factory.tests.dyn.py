from unittest.mock import MagicMock, Mock

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .tested.code import crud_field_view_factory


@mark.fixture
def ctx():
    return Context()


@mark.fixture
def view_factory_reg():
    return MagicMock()


def test_list(view_factory_reg, ctx):
    base_factory_k = htypes.crud_field_view_factory_tests.base_factory_k()
    view_factory_reg.items.return_value = [
        Mock(k=mosaic.put(base_factory_k)),
        ]
    model = htypes.crud_field_view_factory_tests.sample_model()
    form_model = htypes.crud.form_model(
        model=mosaic.put(model),
        record_t=pyobj_creg.actor_to_ref(htypes.crud_field_view_factory_tests.sample_value),
        commit_command_d=mosaic.put(htypes.crud_field_view_factory_tests.sample_d()),
        init_fn=mosaic.put(None),
        args=(),
        )
    k_list = crud_field_view_factory.record_field_list(form_model, ctx, view_factory_reg)
    assert k_list


def test_get(view_factory_reg, ctx):
    base_factory_k = htypes.crud_field_view_factory_tests.base_factory_k()
    k = htypes.crud_field_view_factory.factory_k(
        field_name='str_field',
        field_t=pyobj_creg.actor_to_ref(htypes.builtin.string),
        base_factory_k=mosaic.put(base_factory_k),
        )
    view = crud_field_view_factory.record_field_get(k, ctx, view_factory_reg)
    assert view
