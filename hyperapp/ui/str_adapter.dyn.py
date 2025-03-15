import logging

from .code.mark import mark

log = logging.getLogger(__name__)


class StaticStrAdapter:

    @classmethod
    @mark.actor.ui_adapter_creg
    def from_piece(cls, piece, model, ctx):
        return cls(model)

    def __init__(self, text):
        self._text = text

    @property
    def model(self):
        return self._text

    def get_text(self):
        return self._text

    def text_to_value(self, text):
        return text

    def value_changed(self, new_value):
        if new_value == self._text:
            return
        log.debug("Static str adapter: Ignoring new value: %r", new_value)


@mark.actor.resource_name_creg
def static_str_adapter_resource_name(piece, gen):
    return 'static_str_adapter'
