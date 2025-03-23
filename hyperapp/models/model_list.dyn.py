import logging
from collections import namedtuple
from functools import cached_property
from pathlib import Path

from . import htypes
from .services import (
    pyobj_creg,
    web,
    )
from .code.mark import mark

log = logging.getLogger(__name__)


@mark.model
def model_list_model(piece, model_reg):
    return [
        htypes.model_list.item(
            model_t=pyobj_creg.actor_to_ref(model_t),
            model_t_name=model_t.full_name,
            ui_t=str(web.summon(model.ui_t)),
            fn=str(web.summon(model.system_fn)),
            )
        for model_t, model in model_reg.items()
        ]


@mark.global_command
def open_model_list():
    return htypes.model_list.model()


@mark.actor.formatter_creg
def format_model(piece):
    return "Model list"


@mark.actor.formatter_creg
def format_model_arg(piece):
    model_t = pyobj_creg.invite(piece.model_t)
    return f"Model: {model_t.full_name}"


@mark.selector.get
def model_list_get(value):
    return htypes.model_list.model()


@mark.selector.pick
def model_list_pick(piece, current_item):
    return htypes.model_list.model_arg(
        model_t=current_item.model_t,
        )
