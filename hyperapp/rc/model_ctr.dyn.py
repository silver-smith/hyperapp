from .code.rc_constructor import Constructor


class ModelCtr(Constructor):

    @classmethod
    def from_piece(cls, piece):
        return cls()

    def __init__(self):
        pass

    def update_targets(self, resource_target, target_factory):
        # assert 0, f'todo: {resource_target.name}'
        pass
