from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.view_factory import ViewFactory, ViewMultiFactory
from .tested.code import view_factory_cfg_item


def _sample_fn(view, state):
    return f'sample-fn: {state}'


@mark.fixture
def sample_fn():
    return htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_fn),
        ctx_params=('view', 'state'),
        service_params=(),
        )


@mark.fixture.obj
def template_piece(sample_fn):
    return htypes.view_factory.template(
        model_t_list=None,
        ui_t_t=None,
        view_t=pyobj_creg.actor_to_ref(htypes.view_factory_cfg_item_tests.sample_view),
        is_wrapper=False,
        view_ctx_params=(),
        system_fn=mosaic.put(sample_fn),
        )


@mark.fixture.obj
def multi_template_piece(sample_fn):
    return htypes.view_factory.multi_template(
        model_t_list=None,
        ui_t_t=None,
        list_fn=mosaic.put(sample_fn),
        get_fn=mosaic.put(sample_fn),
        )


def test_template(system, template_piece):
    key = htypes.view_factory_cfg_item_tests.sample_k()
    assert key == htypes.view_factory_cfg_item_tests.sample_k()
    factory = view_factory_cfg_item.resolve_view_factory_cfg_value(template_piece, key, system, '<unused-service-name>')
    assert isinstance(factory, ViewFactory)


def test_multi_template(system, multi_template_piece):
    key = htypes.view_factory_cfg_item_tests.sample_k()
    assert key == htypes.view_factory_cfg_item_tests.sample_k()
    factory = view_factory_cfg_item.resolve_view_multi_factory_cfg_value(multi_template_piece, key, system, '<unused-service-name>')
    assert isinstance(factory, ViewMultiFactory)
