from .code.rc_constructor import Constructor


class ModelCtr(Constructor):

    @classmethod
    def from_piece(cls, piece):
        return cls()

    def __init__(self):
        pass

    def update_resource_targets(self, resource_tgt, target_set):
        # assert 0, f'todo: {resource_target.name}'
        pass
