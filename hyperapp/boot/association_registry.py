import logging
from collections import defaultdict

from hyperapp.boot.htypes.association import association_t

log = logging.getLogger(__name__)


class Association:

    @classmethod
    def from_piece(cls, piece, web):
        return cls(
            bases=[web.summon(base) for base in piece.bases],
            service_name=piece.service_name,
            cfg_item=web.summon(piece.cfg_item),
            )

    def __init__(self, bases, service_name, cfg_item):
        self.bases = bases
        self.service_name = service_name
        self.cfg_item = cfg_item

    @property
    def cfg_item_key(self):
        return (self.service_name, self.cfg_item)

    def to_piece(self, mosaic):
        return association_t(
            bases=tuple(mosaic.put(piece) for piece in self.bases),
            service_name=self.service_name,
            cfg_item=mosaic.put(self.cfg_item),
            )


class AssociationRegistry:

    def __init__(self):
        self._by_base = defaultdict(list)
        self._by_cfg_item_key = {}

    def set_list(self, ass_list):
        for ass in ass_list:
            self._set(ass)

    def set_association(self, bases, service_name, cfg_item):
        ass = Association(bases, service_name, cfg_item)
        self._set(ass)

    def remove_association(self, service_name, cfg_item):
        try:
            ass = self._by_cfg_item_key[service_name, cfg_item]
        except KeyError:
            return
        self._remove(ass)

    def _set(self, ass):
        try:
            ass = self._by_cfg_item_key[ass.cfg_item_key]
        except KeyError:
            pass
        else:
            self._remove(ass)
        self._by_cfg_item_key[ass.cfg_item_key] = ass
        for base in ass.bases:
            self._by_base[base].append(ass)

    def _remove(self, ass):
        del self._by_cfg_item_key[ass.cfg_item_key]
        for base in ass.bases:
            self._by_base[base].remove(ass)
        
    def base_to_ass_list(self, base):
        return self._by_base.get(base, [])
