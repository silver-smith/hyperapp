from . import htypes
from .code.system_fn import ContextFn
from .tested.code import view_factory


def _sample_fn():
    return 'sample-fn'


def test_item(partial_ref):
    system_fn = ContextFn(
        partial_ref=partial_ref, 
        ctx_params=(),
        service_params=(),
        raw_fn=_sample_fn,
        bound_fn=_sample_fn,
        )
    factory = view_factory.ViewFactory(
        k=htypes.view_factory_list_tests.sample_k(),
        view_t=htypes.view_factory_list_tests.sample_view,
        is_wrapper=False,
        view_ctx_params=[],
        system_fn=system_fn,
        )
    assert isinstance(factory.item, htypes.view_factory.item)
