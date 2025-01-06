from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .tested.code import selector as selector_module


def _sample_fn(value):
    return f'sample-fn: {value}'


@mark.fixture.obj
def template_piece():
    system_fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_fn),
        ctx_params=('value',),
        service_params=(),
        )
    return htypes.selector.template(
        value_t=pyobj_creg.actor_to_ref(htypes.selector_tests.sample_value),
        get_fn=mosaic.put(system_fn),
        pick_fn=mosaic.put(system_fn),
        )


def test_template(system, template_piece):
    template = selector_module.SelectorTemplate.from_piece(template_piece)
    selector = template.resolve(system, "<unused service name>")
    assert isinstance(selector, selector_module.Selector)
