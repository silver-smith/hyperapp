import itertools

import yaml

from hyperapp.common.htypes import TRecord

from . import htypes
from .services import (
    deduce_t,
    mosaic,
    pick_refs,
    resource_module_factory,
    resource_registry,
    web,
    )


class LcsResourceStorage:

    _mapping_name = 'lcs_storage_mapping'

    def __init__(self, name, path):
        self._path = path
        self._res_module = resource_module_factory(
            resource_registry, name, path, load_from_file=path.exists())
        self._mapping_cache = None

    def set(self, dir, piece):
        frozen_dir = frozenset(dir)
        for elt in dir:
            self._store(elt)
        self._store(piece)
        self._mapping[frozen_dir] = piece
        self._save()

    def get(self, dir):
        frozen_dir = frozenset(dir)
        return self._mapping.get(frozen_dir)

    def add(self, dir, piece):
        raise NotImplementedError()

    def remove(self, dir):
        raise NotImplementedError()

    def iter(self, filter_dir):
        raise NotImplementedError()

    def _store(self, piece):
        t = deduce_t(piece)
        for ref in pick_refs(t, piece):
            self._store_if_missing(ref)
        name = self._make_name(t)
        self._res_module[name] = piece

    def _store_if_missing(self, ref):
        piece = web.summon(ref)
        if not resource_registry.has_piece(piece):
            self._store(piece)

    @property
    def _mapping(self):
        if self._mapping_cache is not None:
            return self._mapping_cache
        self._mapping_cache = {}
        try:
            mapping = self._res_module[self._mapping_name]
        except KeyError:
            return self._mapping_cache
        for elt in mapping:
            key = frozenset(web.summon(d) for d in elt.key)
            value = web.summon(elt.value)
            self._mapping_cache[key] = value
        return self._mapping_cache

    def _save(self):
        element_list = []
        for key, value in self._mapping.items():
            element = htypes.lcs_resource_storage.element(
                key=tuple(mosaic.put(d) for d in key),
                value=mosaic.put(value),
                )
            element_list.append(element)
        mapping = htypes.lcs_resource_storage.mapping(
            elements=tuple(element_list),
            )
        self._res_module[self._mapping_name] = mapping
        text = yaml.dump(self._res_module.as_dict, sort_keys=False)
        self._path.write_text(text)

    def _make_name(self, t):
        assert isinstance(t, TRecord)
        name = t.name
        for idx in itertools.count(2):
            if name not in self._res_module:
                return name
            name = f'{t.name}_{idx}'
