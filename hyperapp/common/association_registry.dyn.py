import logging
from collections import namedtuple

from . import htypes
from .services import (
    mark,
    meta_registry,
)

log = logging.getLogger(__name__)


Association = namedtuple('Association', 'bases key_to_value')


class AssociationRegistry:

    def __init__(self):
        self._base_to_meta_record = {}
        self._key_to_value = {}

    def register_association_list(self, ass_list):
        for ass in ass_list:
            if isinstance(ass, htypes.meta_registry.meta_association):
                log.info("Register meta association: %r", ass)
                self.register_association(ass)
        for ass in ass_list:
            if not isinstance(ass, htypes.meta_registry.meta_association):
                self.register_association(ass)
    
    def register_association(self, ass):
        log.info("Register association: %r", ass)
        rec = meta_registry.animate(ass)
        log.info("Register association: %r; record: %r", ass, rec)
        if not rec:
            return  # Old-style registration function, registered directly.
        for base in rec.bases:
            self._base_to_meta_record[base] = ass
        for key, value in rec.key_to_value.items():
            self._key_to_value[key] = value

    def __getitem__(self, key):
        return self._key_to_value[key]


@mark.service
def association_reg():
    return AssociationRegistry()


@mark.service
def association():
    return Association
