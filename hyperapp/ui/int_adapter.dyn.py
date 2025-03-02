from .code.mark import mark


class IntAdapter:

    @classmethod
    @mark.actor.ui_adapter_creg
    def from_piece(cls, piece, model, ctx):
        return cls(model)

    def __init__(self, value):
        self._value = value

    @property
    def model(self):
        return self._value

    def get_text(self):
        return str(self._value)

    def text_to_value(self, text):
        return int(text)
