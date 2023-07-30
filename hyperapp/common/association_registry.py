import logging
from collections import defaultdict, namedtuple
from contextlib import contextmanager

log = logging.getLogger(__name__)


Association = namedtuple('Association', 'bases key value')


class AssociationRegistry:

    def __init__(self):
        self._key_to_value = {}
        self._base_to_ass = defaultdict(list)

    @contextmanager
    def associations_registered(self, ass_list):
        added_new = self.register_association_list(ass_list)
        try:
            yield
        finally:
            self.remove_associations(added_new)

    def register_association_list(self, ass_list):
        added_new = []
        for ass in ass_list:
            log.info("Register association: %r", ass)
            if self.register_association(ass):
                added_new.append(ass)
        return added_new
    
    def register_association(self, ass):
        if ass.key in self._key_to_value:
            return False  # Already registered.
        self._key_to_value[ass.key] = ass.value
        for base in ass.bases:
            self._base_to_ass[base].append(ass)
        return True

    def remove_associations(self, ass_list):
        for ass in ass_list:
            try:
                del self._key_to_value[ass.key]
            except KeyError:
                pass
            else:
                for base in ass.bases:
                    self._base_to_ass[ass.base].remove(ass)

    def __contains__(self, key):
        return key in self._key_to_value

    def __getitem__(self, key):
        return self._key_to_value[key]

    def base_to_ass_list(self, base):
        return self._base_to_ass.get(base, [])
