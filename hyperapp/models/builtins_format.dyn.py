from .services import (
    web,
    )
from .code.mark import mark


@mark.actor.formatter_creg
def format_attribute(piece, format):
    object = web.summon(piece.object)
    object_title = format(object)
    return f"attr({object_title}.{piece.attr_name})"


@mark.actor.formatter_creg
def format_python_module(piece, format):
    return f"module({piece.module_name})"
