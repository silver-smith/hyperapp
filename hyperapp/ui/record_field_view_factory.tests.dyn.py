from unittest.mock import MagicMock, AsyncMock

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .code.system_fn import ContextFn
from .tested.code import record_field_view_factory


def sample_record_model():
    pass


@mark.fixture
def sample_record_model_fn(rpc_system_call_factory):
    return ContextFn(
        rpc_system_call_factory=rpc_system_call_factory,
        ctx_params=(),
        service_params=(),
        raw_fn=sample_record_model,
        )


@mark.fixture
def ctx():
    return Context()


@mark.fixture
def view_factory_reg():
    reg = MagicMock()
    reg.__getitem__.return_value = AsyncMock()
    return reg


@mark.fixture
def factory_k(sample_record_model_fn):
    base_factory_k = htypes.record_field_view_factory_tests.base_factory_k()
    return htypes.record_field_view_factory.factory_k(
        field_name='str_field',
        field_t=pyobj_creg.actor_to_ref(htypes.builtin.string),
        record_t=pyobj_creg.actor_to_ref(htypes.record_field_view_factory_tests.sample_model),
        system_fn=mosaic.put(sample_record_model_fn.piece),
        base_factory_k=mosaic.put(base_factory_k),
        )


def test_format(factory_k):
    result = record_field_view_factory.format_factory_k(factory_k)
    assert result.startswith('str_field:')


def test_list(view_factory_reg, ctx, sample_record_model_fn):
    base_factory_k = htypes.record_field_view_factory_tests.base_factory_k()
    view_factory_reg.items.return_value = [
        AsyncMock(k=mosaic.put(base_factory_k)),
        ]
    ui_t = htypes.model.record_ui_t(
        record_t=pyobj_creg.actor_to_ref(htypes.record_field_view_factory_tests.sample_model),
        )
    k_list = record_field_view_factory.record_field_list(ui_t, sample_record_model_fn, ctx, view_factory_reg)
    assert k_list


async def test_get(view_factory_reg, ctx, factory_k):
    view = await record_field_view_factory.record_field_get(factory_k, ctx, view_factory_reg)
    assert view
