import yaml

from hyperapp.common.htypes import TPrimitive, TRecord

from . import htypes
from .services import (
    deduce_t,
    mosaic,
    pick_refs,
    resource_module_factory,
    resource_registry,
    web,
    )


MAX_SAME_NAME_COUNT = 1000


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
        try:
            prev_piece = self._mapping[frozen_dir]
        except KeyError:
            pass
        else:
            self._remove_piece(prev_piece)
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

    def _remove_piece(self, piece):
        t = deduce_t(piece)
        for name in self._existing_names(t):
            if self._res_module[name] == piece:
                del self._res_module[name]

    def _store(self, piece):
        t = deduce_t(piece)
        self._store_if_missing(piece, t)

    def _store_if_missing(self, piece, t):
        if resource_registry.has_piece(piece):
            return
        for ref in pick_refs(piece):
            elt_piece, elt_t = web.summon_with_t(ref)
            self._store_if_missing(elt_piece, elt_t)
        name = self._make_name(t)
        self._res_module[name] = piece

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

    def _iter_names(self, t):
        if isinstance(t, TPrimitive):
            stem = t.name
        else:
            assert isinstance(t, TRecord)
            stem = t.name
            if stem in {'view', 'layout', 'state', 'adapter'}:
                mnl = t.module_name.split('.')
                stem = f'{mnl[-1]}_{t.name}'
        for idx in range(1, MAX_SAME_NAME_COUNT):
            yield f'{stem}_{idx}'


    def _existing_names(self, t):
        for name in self._iter_names(t):
            if name in self._res_module:
                yield name

    def _make_name(self, t):
        for name in self._iter_names(t):
            if name not in self._res_module:
                return name
