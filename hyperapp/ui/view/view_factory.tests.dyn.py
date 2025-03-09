from . import htypes
from .services import (
    web,
    )
from .code.mark import mark
from .code.context import Context
from .code.system_fn import ContextFn
from .tested.code import view_factory


def _sample_fn():
    return 'sample-fn'


@mark.fixture
def ctx():
    return Context()


def test_service(view_factory_reg, ctx):
    factory_reg = view_factory_reg()
    assert factory_reg.items(ctx, model=None) == []


def test_item(partial_ref, visualizer_reg):
    system_fn = ContextFn(
        partial_ref=partial_ref, 
        ctx_params=(),
        service_params=(),
        raw_fn=_sample_fn,
        bound_fn=_sample_fn,
        )
    factory = view_factory.ViewFactory(
        visualizer_reg=visualizer_reg,
        k=htypes.view_factory_tests.sample_k(),
        model_t=None,
        ui_t_t=None,
        view_t=htypes.view_factory_tests.sample_view,
        is_wrapper=False,
        view_ctx_params=[],
        system_fn=system_fn,
        )
    assert isinstance(factory.item, htypes.view_factory.item)


def _sample_list():
    return [htypes.view_factory_tests.sample_item_k()]


def _sample_get(k):
    assert isinstance(k, htypes.view_factory_tests.sample_item_k)


def test_multi_key(partial_ref, visualizer_reg, ctx):
    list_fn = ContextFn(
        partial_ref=partial_ref, 
        ctx_params=(),
        service_params=(),
        raw_fn=_sample_list,
        bound_fn=_sample_list,
        )
    get_fn = ContextFn(
        partial_ref=partial_ref, 
        ctx_params=(),
        service_params=(),
        raw_fn=_sample_get,
        bound_fn=_sample_get,
        )
    factory = view_factory.ViewMultiFactory(
        visualizer_reg=visualizer_reg,
        k=htypes.view_factory_tests.sample_k(),
        model_t=None,
        ui_t_t=None,
        list_fn=list_fn,
        get_fn=get_fn,
        )
    model = "Sample model"
    item_list = factory.get_item_list(ctx, model)
    assert len(item_list) == 1
    k = web.summon(item_list[0].k)
    assert isinstance(k, htypes.view_factory.multi_item_k)
