from . import htypes
from .services import (
    mosaic,
    )


class FixtureCtr:

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.attr_name, piece.name)

    def __init__(self, attr_name, name):
        self._attr_name = attr_name
        self._name = name

    def update_targets(self, resource_target, target_set):
        pass

    def make_component(self, python_module, name_to_res=None):
        assert 0

    def get_component(self, name_to_res):
        assert 0
