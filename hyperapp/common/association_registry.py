import logging
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from hyperapp.common.htypes.association import association_t

log = logging.getLogger(__name__)


@dataclass
class Association:
    bases: list[Any]
    key: Any
    value: Any

    @classmethod
    def from_piece(cls, piece, web):
        key = tuple(web.summon(ref) for ref in piece.key)
        if len(piece.key) == 1:
            [key] = key
        return cls(
            bases=[web.summon(ref) for ref in piece.bases],
            key=key,
            value=web.summon(piece.value),
            )

    def to_piece(self, mosaic):
        if type(self.key) in {tuple, list}:
            key = self.key
        else:
            key = [self.key]
        return association_t(
            bases=[mosaic.put(piece) for piece in self.bases],
            key=[mosaic.put(piece) for piece in key],
            value=mosaic.put(self.value),
            )


class AssociationRegistry:

    def __init__(self):
        self._key_to_values = defaultdict(list)
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
        if ass.value in self._key_to_values.get(ass.key, []):
            return False  # Already registered.
        self._key_to_values[ass.key].append(ass.value)
        for base in ass.bases:
            self._base_to_ass[base].append(ass)
        return True

    def remove_associations(self, ass_list):
        for ass in ass_list:
            try:
                self._key_to_values.get(ass.key, []).remove(ass.value)
            except ValueError:
                pass
            else:
                for base in ass.bases:
                    self._base_to_ass[base].remove(ass)

    def __contains__(self, key):
        return key in self._key_to_values

    def __getitem__(self, key):
        values = self.get_all(key)
        if len(values) == 0:
            raise KeyError(key)
        if len(values) > 1:
            raise RuntimeError(f"Multiple values are registered for key {key!r}, while expected just one: {values}")
        return values[0]

    def get_all(self, key):
        return self._key_to_values.get(key, [])
        
    def base_to_ass_list(self, base):
        return self._base_to_ass.get(base, [])
