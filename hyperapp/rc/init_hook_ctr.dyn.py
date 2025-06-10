from .code.rc_constructor import Constructor


class InitHookCtr(Constructor):

    @classmethod
    def from_template_piece(cls, piece, service_name, var_name):
        return cls(var_name)

    def __init__(self, var_name):
        self._var_name = var_name

    def get_component(self, name_to_res):
        return name_to_res[self._var_name]

    @property
    def key(self):
        return self._var_name.rsplit('.', 1)[0]
