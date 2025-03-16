import logging
from collections import namedtuple
from functools import cached_property
from pathlib import Path

from . import htypes
from .services import (
    web,
    )
from .code.mark import mark

log = logging.getLogger(__name__)


@mark.model
def model_list_model(piece, model_reg):
    return [
        htypes.model_list.item(
            model_t=model_t.full_name,
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
