from . import htypes
from .services import (
    pyobj_creg,
    mosaic,
    )
from .code.mark import mark
from .code.system_fn import ContextFn
from .code.view_factory import ViewFactory
from .tested.code import view_factory_list


def _sample_fn():
    return 'sample-fn'


@mark.config_fixture('view_factory_reg')
def view_factory_reg_config(partial_ref):
    system_fn = ContextFn(
        partial_ref=partial_ref, 
        ctx_params=(),
        service_params=(),
        raw_fn=_sample_fn,
        bound_fn=_sample_fn,
        )
    factory = ViewFactory(
        d=htypes.view_factory_list_tests.sample_d(),
        view_t=htypes.view_factory_list_tests.sample_view,
        is_wrapper=False,
        view_ctx_params=[],
        system_fn=system_fn,
        )
    return {factory.d: factory}


@mark.fixture
def piece():
    return htypes.view_factory_list.view()


def test_view_factory_list(piece):
    items = view_factory_list.view_factory_list(piece)
    assert items


def test_open():
    piece = view_factory_list.open_view_factory_list()
    assert isinstance(piece, htypes.view_factory_list.view)
