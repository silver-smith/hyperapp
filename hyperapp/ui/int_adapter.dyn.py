
class IntAdapter:

    @classmethod
    def from_piece(cls, piece, model, ctx):
        return cls(model)

    def __init__(self, value):
        self._value = value

    @property
    def model(self):
        return self._value

    def get_text(self):
        return str(self._value)
