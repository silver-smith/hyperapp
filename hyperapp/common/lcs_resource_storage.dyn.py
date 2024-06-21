import itertools

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


class LcsResourceStorage:

    _mapping_name = 'lcs_storage_mapping'

    def __init__(self, name, path):
        self._path = path
        self._res_module = resource_module_factory(
            resource_registry, name, path, load_from_file=path.exists())
        self._mapping = self._load_mapping()

    def set(self, dir, piece):
        fdir = frozenset(dir)
        self._mapping[fdir] = piece
        self._save()

    def get(self, dir):
        fdir = frozenset(dir)
        return self._mapping.get(fdir)

    def add(self, dir, piece):
        raise NotImplementedError()

    def remove(self, dir):
        raise NotImplementedError()

    def iter(self, filter_dir):
        raise NotImplementedError()

    def _load_mapping(self):
        try:
            mapping_recs = self._res_module[self._mapping_name]
        except KeyError:
            return {}
        mapping = {}
        for elt in mapping_recs:
            key = frozenset(web.summon(d) for d in elt.key)
            value = web.summon(elt.value)
            mapping[key] = value
        return mapping

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

    def _save(self):
        # We should remove not only old values from mapping,
        # but also now-unused elements they reference.
        # Thus, construct it from afresh every time.
        self._res_module.clear()
        element_list = []
        for key, value in self._mapping.items():
            for elt in key:
                self._store(elt)
            self._store(value)
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
        for idx in itertools.count(1):
            yield f'{stem}_{idx}'

    def _make_name(self, t):
        for name in self._iter_names(t):
            if name not in self._res_module:
                return name
