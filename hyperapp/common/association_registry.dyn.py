from collections import namedtuple

from hyperapp.common.htypes.deduce_value_type import deduce_value_type

from .services import (
    mark,
    meta_registry,
)


Association = namedtuple('Association', 'bases key_to_value')


class AssociationRegistry:

    def __init__(self):
        self._base_to_meta_record = {}
        self._type_key_to_value = {}

    def register_meta_association(self, meta_ass):
        t = deduce_value_type(meta_ass)
        ass = meta_registry.animate(meta_ass)
        for base in ass.bases:
            self._base_to_meta_record[base] = meta_ass
        for key, value in ass.key_to_value.items():
            self._type_key_to_value[t, key] = value


@mark.service
def association_reg():
    return AssociationRegistry()
