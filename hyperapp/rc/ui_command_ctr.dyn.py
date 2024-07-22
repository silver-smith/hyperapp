from .code.rc_constructor import Constructor


class UiCommandCtr(Constructor):

    @classmethod
    def from_piece(cls, piece):
        return cls()

    def __init__(self):
        pass


class UniversalUiCommandCtr(Constructor):

    @classmethod
    def from_piece(cls, piece):
        return cls()

    def __init__(self):
        pass


class UiModelCommandCtr(Constructor):

    @classmethod
    def from_piece(cls, piece):
        return cls()

    def __init__(self):
        pass

class UniversalUiModelCommandCtr(Constructor):

    @classmethod
    def from_piece(cls, piece):
        return cls()

    def __init__(self):
        pass
