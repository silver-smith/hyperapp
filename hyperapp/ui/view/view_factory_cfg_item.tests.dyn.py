from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.view_factory import ViewFactory
from .tested.code import view_factory_cfg_item


def _sample_fn(view, state):
    return f'sample-fn: {state}'


@mark.fixture.obj
def template_piece():
    system_fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_fn),
        ctx_params=('view', 'state'),
        service_params=(),
        )
    return htypes.view_factory.template(
        k=mosaic.put(htypes.view_factory_cfg_item_tests.sample_k()),
        view_t=pyobj_creg.actor_to_ref(htypes.view_factory_cfg_item_tests.sample_view),
        is_wrapper=False,
        view_ctx_params=(),
        system_fn=mosaic.put(system_fn),
        )


def test_cfg_item(system, template_piece):
    template = view_factory_cfg_item.ViewFactoryTemplate.from_piece(template_piece)
    factory = template.resolve(system, "<unused service name>")
    assert isinstance(factory, ViewFactory)
