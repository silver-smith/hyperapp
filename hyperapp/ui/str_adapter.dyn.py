

class StaticStrAdapter:

    @classmethod
    def from_piece(cls, piece, ctx):
        return cls(piece.value)

    def __init__(self, text):
        self._text = text

    @property
    def model(self):
        return self._text

    def get_text(self):
        return self._text
