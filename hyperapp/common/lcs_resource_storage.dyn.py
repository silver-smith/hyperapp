import itertools

import yaml

from hyperapp.common.htypes import TRecord

from .services import (
    deduce_t,
    resource_module_factory,
    resource_registry,
    )


class LcsResourceStorage:

    def __init__(self, name, path=None):
        self._path = path
        self._res_module = resource_module_factory(resource_registry, name, path, load_from_file=False)

    def set(self, dir, piece):
        frozen_dir = frozenset(dir)
        name = self._make_name(piece)
        self._res_module[name] = piece
        self._save()

    def get(self, dir):
        frozen_dir = frozenset(dir)

    def _save(self):
        text = yaml.dump(self._res_module.as_dict, sort_keys=False)
        self._path.write_text(text)

    def _make_name(self, piece):
        t = deduce_t(piece)
        assert isinstance(t, TRecord)
        name = t.name
        for idx in itertools.count(2):
            if name not in self._res_module:
                return name
            name = f'{t.name}_{idx}'
