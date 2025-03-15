from .code.rc_constructor import Constructor


class MarkerCtr(Constructor):

    @classmethod
    def from_template_piece(cls, piece, service_name):
        return cls(piece.name)

    def __init__(self, name):
        self._name = name

    def get_component(self, name_to_res):
        return name_to_res[f'{self._name}.marker-template']
