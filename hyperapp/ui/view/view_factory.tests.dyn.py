from . import htypes
from .services import (
    web,
    )
from .code.mark import mark
from .code.context import Context
from .code.system_fn import ContextFn
from .tested.code import view_factory


def _sample_fn(model_t, accessor):
    assert model_t is htypes.builtin.string
    assert accessor == htypes.accessor.model_accessor()
    return 'sample-fn'


@mark.fixture.obj
def model():
    return "Sample model"


@mark.fixture
def ctx(model):
    return Context(
        model=model,
        )


def test_service(view_factory_reg, ctx):
    factory_reg = view_factory_reg()
    assert factory_reg.items(ctx, model=None) == []


async def test_item(rpc_system_call_factory, format, visualizer_reg, ctx):
    system_fn = ContextFn(
        rpc_system_call_factory=rpc_system_call_factory,
        ctx_params=('model_t', 'accessor'),
        service_params=(),
        raw_fn=_sample_fn,
        )
    factory = view_factory.ViewFactory(
        format=format,
        visualizer_reg=visualizer_reg,
        k=htypes.view_factory_tests.sample_k(),
        model_t_list=[htypes.builtin.string],
        ui_t_t=None,
        view_t=htypes.view_factory_tests.sample_view,
        is_wrapper=False,
        view_ctx_params=[],
        system_fn=system_fn,
        )
    assert isinstance(factory.item, htypes.view_factory.item)
    result = await factory.call(ctx)
    assert result == 'sample-fn'


def _sample_list():
    return [htypes.view_factory_tests.sample_item_k()]


def _sample_get(k):
    assert isinstance(k, htypes.view_factory_tests.sample_item_k)


def test_multi_key(rpc_system_call_factory, format, visualizer_reg, model, ctx):
    list_fn = ContextFn(
        rpc_system_call_factory=rpc_system_call_factory,
        ctx_params=(),
        service_params=(),
        raw_fn=_sample_list,
        )
    get_fn = ContextFn(
        rpc_system_call_factory=rpc_system_call_factory,
        ctx_params=(),
        service_params=(),
        raw_fn=_sample_get,
        )
    factory = view_factory.ViewMultiFactory(
        format=format,
        visualizer_reg=visualizer_reg,
        k=htypes.view_factory_tests.sample_k(),
        model_t_list=None,
        ui_t_t=None,
        list_fn=list_fn,
        get_fn=get_fn,
        )
    item_list = factory.get_item_list(ctx, model, ui_t=None, system_fn=None)
    assert len(item_list) == 1
    k = web.summon(item_list[0].k)
    assert isinstance(k, htypes.view_factory.multi_item_k)
