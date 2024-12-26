import itertools

import re
import yaml

from hyperapp.common.htypes import TPrimitive, TRecord, tString

from . import htypes
from .services import (
    deduce_t,
    mosaic,
    resource_module_factory,
    resource_registry,
    web,
    )
from .code.mark import mark


class LcsResourceStorage:

    _mapping_name = 'lcs_storage_mapping'
    _shortcut_re = re.compile(r'([A-Z][A-Za-z]*\+)*[A-Z][A-Za-z0-9]*$')

    def __init__(self, pick_refs, name, path):
        self._pick_refs = pick_refs
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
        fdir = frozenset(dir)
        del self._mapping[fdir]
        self._save()

    def items(self, filter_dir=None):
        return self._mapping.items()

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
        for ref in self._pick_refs(piece):
            elt_piece, elt_t = web.summon_with_t(ref)
            self._store_if_missing(elt_piece, elt_t)
        name = self._make_name(piece, t)
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
                key=tuple(sorted(mosaic.put(d) for d in key)),
                value=mosaic.put(value),
                )
            element_list.append(element)
        mapping = htypes.lcs_resource_storage.mapping(
            elements=tuple(element_list),
            )
        self._res_module[self._mapping_name] = mapping
        text = yaml.dump(self._res_module.as_dict, sort_keys=False)
        self._path.write_text(text)

    def _require_index(self, t, piece, stem):
        if t is tString and self._shortcut_re.match(piece):
            return False
        if not isinstance(t, TRecord):
            return True
        if t.name == stem:
            # Custom type name is added to resource module by type name.
            # If it matches value name, index suffix should be added to avoid name clash.
            return True
        return t.fields

    def _make_stem(self, piece, t=None):
        if t is None:
            t = deduce_t(piece)
        if t is tString and self._shortcut_re.match(piece):
            return 'shortcut_' + piece.replace('+', '_')
        elif isinstance(t, TPrimitive):
            return t.name
        else:
            assert isinstance(t, TRecord)
            if t.name in {'view', 'layout', 'state', 'adapter'}:
                mnl = t.module_name.split('.')
                return f'{mnl[-1]}_{t.name}'
            if t is htypes.builtin.record_mt:
                return f'{piece.name}_record_mt'
            if t is htypes.builtin.call:
                fn = web.summon(piece.function)
                base_stem = self._make_stem(fn)
                return f'{base_stem}_call'
            return t.name

    def _iter_names(self, piece, t):
        stem = self._make_stem(piece, t)
        if not self._require_index(t, piece, stem):
            yield stem
            if isinstance(t, TRecord):
                yield f'{t.module_name}.{stem}'
            return
        for idx in itertools.count(1):
            yield f'{stem}_{idx}'

    def _make_name(self, piece, t):
        tried_names = []
        for name in self._iter_names(piece, t):
            if name not in self._res_module:
                return name
            tried_names.append(name)
        raise RuntimeError(f"All names ({', '.join(tried_names)}) for piece {piece!r} are already in use")


@mark.service
def lcs_resource_storage_factory(pick_refs, name, path):
    return LcsResourceStorage(pick_refs, name, path)
