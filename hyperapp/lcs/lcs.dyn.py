import logging
import weakref
from collections import defaultdict

import yaml
from pathlib import Path

from .services import (
    hyperapp_dir,
    )
from .code.directory import name_to_d

log = logging.getLogger(__name__)


class LCSheet:

    @classmethod
    def from_layer_list_path(cls, path, lcs_resource_storage_factory):
        try:
            data = yaml.safe_load(path.read_text())
        except FileNotFoundError:
            data = None
        return cls(data, lcs_resource_storage_factory)

    def __init__(self, layers_data, lcs_resource_storage_factory):
        self._name_to_storage = {}
        self._d_to_storage = {}
        self._default_layer_name = None
        self._default_storage = None
        self._d_to_w_to_ap = defaultdict(weakref.WeakKeyDictionary)
        self._load(layers_data, lcs_resource_storage_factory)

    def get(self, dir, default=None):
        for storage in self._d_to_storage.values():
            piece = storage.get(dir)
            if piece is not None:
                return piece
        return default

    def set(self, dir, piece):
        log.info("LCS: set to %s: %s -> %s", self._default_layer_name, set(dir), piece)
        self._default_storage.set(dir, piece)

    def __iter__(self):
        for layer_d, storage in self._d_to_storage.items():
            for d_set, piece in storage.items():
                yield (layer_d, d_set, piece)

    def layers(self):
        return self._d_to_storage.keys()

    def apply(self, dir, widget, ap):
        fdir = frozenset(dir)
        w_to_ap = self._d_to_w_to_ap[fdir]
        ap_set = w_to_ap.setdefault(widget, set())
        ap_set.add(ap)
        value = self.get(dir)
        if value is not None:
            return ap.apply(widget, value)
        ap.clear(widget)
        return False

    def move(self, dir, source_layer_d, target_layer_d):
        log.info("Move %s from %s to %s", dir, source_layer_d, target_layer_d)
        source_storage = self._d_to_storage[source_layer_d]
        target_storage = self._d_to_storage[target_layer_d]
        piece = source_storage.get(dir)
        if piece is None:
            log.warning("Dir %s is missing from %s", dir, source_layer_d)
            return
        # Should remove first. Overwise, resources from new storage would reference
        # resources from old one. And those are removed.
        source_storage.remove(dir)
        target_storage.set(dir, piece)

    def _load(self, data, lcs_resource_storage_factory):
        if not data:
            return
        for layer in data['layers']:
            name = layer['name']
            path = hyperapp_dir / Path(layer['path']).expanduser()
            d = name_to_d('lcs_layer', name.replace('.', '_'))
            storage = lcs_resource_storage_factory(name, path)
            self._name_to_storage[name] = storage
            self._d_to_storage[d] = storage
        self._default_layer_name = data['default_layer']
        self._default_storage = self._name_to_storage[self._default_layer_name]
