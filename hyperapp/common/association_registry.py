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
            bases=tuple(web.summon(ref) for ref in piece.bases),
            key=key,
            value=web.summon(piece.value),
            )

    def to_piece(self, mosaic):
        if type(self.key) in {tuple, list}:
            key = self.key
        else:
            key = [self.key]
        return association_t(
            bases=tuple(mosaic.put(piece) for piece in self.bases),
            key=tuple(mosaic.put(piece) for piece in key),
            value=mosaic.put(self.value),
            )


class AssociationRegistry:

    def __init__(self):
        self._key_to_values = defaultdict(list)
        self._key_to_ass = defaultdict(list)
        self._base_to_ass = defaultdict(list)

    @contextmanager
    def associations_registered(self, ass_list, override):
        added, overridden = self.register_association_list(ass_list, override)
        try:
            yield
        finally:
            self.remove_associations(added)
            self.register_association_list(overridden)

    def register_association_list(self, ass_list, override=False):
        added_list = []
        overridden_list = []
        for ass in ass_list:
            log.info("Register association: %r", ass)
            is_registered, overridden = self.register_association(ass, override)
            if is_registered:
                added_list.append(ass)
                overridden_list += overridden
        return (added_list, overridden_list)
    
    def register_association(self, ass, override=False):
        if ass.value in self._key_to_values.get(ass.key, []):
            return (False, [])  # Already registered.
        if override:
            overridden = self._key_to_ass[ass.key]
            self.remove_associations(overridden)
        else:
            overridden = []
        self._key_to_values[ass.key].append(ass.value)
        self._key_to_ass[ass.key].append(ass)
        for base in ass.bases:
            self._base_to_ass[base].append(ass)
        return (True, overridden)

    def remove_associations(self, ass_list):
        for ass in ass_list:
            try:
                self._key_to_values.get(ass.key, []).remove(ass.value)
            except ValueError:
                pass
            else:
                self._key_to_ass[ass.key].remove(ass)
                for base in ass.bases:
                    self._base_to_ass[base].remove(ass)

    def __contains__(self, key):
        return key in self._key_to_values

    def __getitem__(self, key):
        value_list = self.get_all(key)
        if len(value_list) == 0:
            raise KeyError(key)
        if len(value_list) == 1:
            return value_list[0]
        value = value_list[0]
        log.warning(
            f"Picking random single value %r for key %r while multiple values are registered: %r",
            value, key, value_list)
        return value

    def get_all(self, key):
        return self._key_to_values.get(key, [])
        
    def base_to_ass_list(self, base):
        return self._base_to_ass.get(base, [])
