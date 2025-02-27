from . import htypes
from .services import (
    pyobj_creg,
    mosaic,
    )
from .code.mark import mark
from .code.context import Context
from .code.system_fn import ContextFn
from .code.view_factory import ViewFactory
from .code.multi_actor_template import MultiActorItem
from .tested.code import view_factory_list


def _sample_fn():
    return 'sample-fn'


@mark.fixture
def factory(partial_ref):
    system_fn = ContextFn(
        partial_ref=partial_ref, 
        ctx_params=(),
        service_params=(),
        raw_fn=_sample_fn,
        bound_fn=_sample_fn,
        )
    return ViewFactory(
        k=htypes.view_factory_list_tests.sample_k(),
        view_t=htypes.view_factory_list_tests.sample_view,
        is_wrapper=False,
        view_ctx_params=[],
        system_fn=system_fn,
        )


@mark.config_fixture('view_factory_reg')
def view_factory_reg_config(factory):
    return {factory.k: factory}


@mark.fixture
def piece():
    return htypes.view_factory_list.model(
        model_t=None,
        )


def test_view_factory_list(factory, piece):
    items = view_factory_list.view_factory_list(piece)
    assert items == [factory.item]


@mark.config_fixture('visualizer_reg')
def visualizer_config():
    ui_t = htypes.view_factory_list_tests.sample_ui_t()
    return {
        htypes.view_factory_list_tests.sample_model: htypes.model.model(
            ui_t=mosaic.put(ui_t),
            system_fn=mosaic.put(None),
            ),
        }


@mark.config_fixture('adapter_creg')
def adapter_creg_config():
    return {
        htypes.view_factory_list_tests.sample_ui_t: [
            MultiActorItem(
                k=htypes.view_factory_list_tests.layout_k(),
                t=htypes.view_factory_list_tests.sample_ui_t,
                fn=None,
                ),
            ],
        }


def test_view_factory_list_with_model(factory):
    piece = htypes.view_factory_list.model(
        model_t=pyobj_creg.actor_to_ref(htypes.view_factory_list_tests.sample_model),
        )
    items = view_factory_list.view_factory_list(piece)
    assert len(items) == 2
    assert factory.item in items
    k = htypes.view_factory_list_tests.layout_k()
    assert mosaic.put(k) in {item.k for item in items}


def test_open():
    piece = view_factory_list.open_view_factory_list()
    assert isinstance(piece, htypes.view_factory_list.model)


def test_editor_default():
    ctx = Context()
    context = view_factory_list.pick_view_factory_context(ctx)


def test_selector_get():
    k = htypes.view_factory_list_tests.sample_k(),
    value = htypes.view_factory.factory(
        model_t=None,
        k=mosaic.put(k),
        )
    piece = view_factory_list.view_factory_list_get(value)
    assert piece


def test_selector_pick():
    k = htypes.view_factory_list_tests.sample_k(),
    current_item = htypes.view_factory.item(
        k=mosaic.put(k),
        k_str="<unused>",
        view_t=mosaic.put("<unused>"),
        view_t_str="<unused>",
        is_wrapper=False,
        view_ctx_params=(),
        model_t=None,
        system_fn=mosaic.put("<unused>"),
        )
    factory = view_factory_list.view_factory_list_pick(piece, current_item)
    assert isinstance(factory, htypes.view_factory.factory)
