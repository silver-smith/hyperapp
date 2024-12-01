from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .tested.code import rename_command


@mark.fixture
def piece():
    model = htypes.rename_command_tests.sample_model()
    model_state = htypes.rename_command_tests.sample_model_state()
    return htypes.model_commands.view(
        model=mosaic.put(model),
        model_state=mosaic.put(model_state)
        )


@mark.fixture
def d_ref(data_to_ref):
    d = htypes.rename_command_tests.sample_command_d()
    return data_to_ref(d)


def test_get(piece, d_ref):
    form = rename_command.model_command_get(piece, d_ref)
    assert form.name == 'sample_command'


def test_update(piece, d_ref):
    form = htypes.rename_command.form(
        name='new_name',
        )
    rename_command.model_command_update(piece, d_ref, form)
