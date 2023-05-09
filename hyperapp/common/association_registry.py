import logging
from collections import defaultdict, namedtuple

from .htypes.meta_association import meta_association

log = logging.getLogger(__name__)


Association = namedtuple('Association', 'bases key_to_value')


class AssociationRegistry:

    def __init__(self, meta_registry):
        self._meta_registry = meta_registry
        self._base_to_meta_record = defaultdict(set)
        self._key_to_value = {}

    def register_association_list(self, ass_list):
        for ass in ass_list:
            if isinstance(ass, meta_association):
                log.info("Register meta association: %r", ass)
                self.register_association(ass)
        for ass in ass_list:
            if not isinstance(ass, meta_association):
                self.register_association(ass)
    
    def register_association(self, ass):
        log.info("Register association: %r", ass)
        rec = self._meta_registry.animate(ass)
        log.info("Register association: %r; record: %r", ass, rec)
        if not rec:
            return  # Old-style registration function, registered directly.
        for base in rec.bases:
            self._base_to_meta_record[base].add(ass)
        for key, value in rec.key_to_value.items():
            self._key_to_value[key] = value

    # TODO: Remove associations after use in runner.
    # def remove_associations(self, ass_list):
    #     for ass in ass_list:
    #         for base, ass_set in self._base_to_meta_record:
    #             self._base_to_meta_record[base] = ass_set - set(ass_list)
    #         for key, value in list(self._key_to_value.items()):
    #             if ???

    def __getitem__(self, key):
        return self._key_to_value[key]

    def associations_for_base(self, base):
        return self._base_to_meta_record.get(base, [])
