from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .tested.code import record_field_view_factory


def test_list():
    model = htypes.record_field_view_factory_tests.sample_model()
    form_model = htypes.crud.form_model(
        model=mosaic.put(model),
        record_t=pyobj_creg.actor_to_ref(htypes.record_field_view_factory_tests.sample_value),
        commit_command_d=mosaic.put(htypes.record_field_view_factory_tests.sample_d()),
        init_fn=mosaic.put(None),
        args=(),
        )
    k_list = record_field_view_factory.record_field_list(form_model)
    assert k_list
