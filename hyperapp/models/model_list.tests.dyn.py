from . import htypes
from .services import (
    pyobj_creg,
    )
from .tested.code import model_list
from .code.mark import mark


@mark.fixture
def piece():
    return htypes.model_list.model()


def test_model(piece):
    item_list = model_list.model_list_model(piece)
    assert type(item_list) is list


def test_open():
    piece = model_list.open_model_list()
    assert piece


def test_format_model(piece):
    title = model_list.format_model(piece)
    assert type(title) is str


def test_format_model_arg():
    value = htypes.model_list.model_arg(
        model_t=pyobj_creg.actor_to_ref(htypes.builtin.string),
        )
    title = model_list.format_model_arg(value)
    assert type(title) is str


def test_selector_get():
    value = htypes.model_list.model_arg(
        model_t=pyobj_creg.actor_to_ref(htypes.builtin.string),
        )
    piece = model_list.model_list_get(value)
    assert piece


def test_selector_pick(piece):
    current_item = htypes.model_list.item(
        model_t=pyobj_creg.actor_to_ref(htypes.builtin.string),
        model_t_name="<unused>",
        ui_t="<unused>",
        fn="<unused>",
        )
    value = model_list.model_list_pick(piece, current_item)
    assert value == htypes.model_list.model_arg(
        model_t=pyobj_creg.actor_to_ref(htypes.builtin.string),
        )
