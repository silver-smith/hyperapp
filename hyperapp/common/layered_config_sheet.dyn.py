import logging
from dataclasses import dataclass, field
from typing import List
from pathlib import Path

from . import htypes
from .module import ClientModule

log = logging.getLogger(__name__)


lcs_path = Path('~/.local/share/hyperapp/client/lcs.cdr').expanduser()


@dataclass
class Record:
    value_list: List = field(default_factory=list)
    is_multi_value: bool = False
    persist: bool = False

    @classmethod
    def from_piece(cls, piece, web, persist):
        dir = [
            web.summon(ref)
            for ref in piece.dir
            ]
        value_list = [
            web.summon(ref)
            for ref in piece.value_list
            ]
        record = cls(value_list, piece.is_multi_value, persist)
        return (dir, record)

    def as_piece(self, dir, mosaic):
        dir_refs = [
            mosaic.put(element)
            for element in dir
            ]
        values_refs = [
            mosaic.put(element)
            for element in self.value_list
            ]
        return htypes.layered_config_sheet.lcs_association(dir_refs, self.is_multi_value, values_refs)


class LCSlice:

    def __init__(self, dir_to_record=None):
        self._dir_to_record = dir_to_record or {}

    def get(self, dir):
        try:
            record = self._dir_to_record[frozenset(dir)]
        except KeyError:
            return None
        except TypeError as x:
            raise RuntimeError(f"LCS: Type error: {x}: {dir!r}")
        if record.is_multi_value:
            raise RuntimeError(f"LCS: Attempt to get single value from multi-value record: {set(dir)}")
        return record.value_list[0]


class LCSheet(LCSlice):

    def __init__(self, mosaic, web, bundle):
        super().__init__()
        self._mosaic = mosaic
        self._web = web
        self._bundle = bundle
        self._load()

    def _load(self):
        try:
            storage = self._bundle.load_piece()
        except FileNotFoundError:
            pass
        else:
            for association in storage.record_list:
                dir, record = Record.from_piece(association, self._web, persist=True)
                log.info("LCS: loaded %s -> %s", set(dir), record)
                self._set(dir, record)

    def _save(self):
        rec_list = [
            record.as_piece(dir, self._mosaic)
            for dir, record
            in self._dir_to_record.items()
            if record.persist
            ]
        self._bundle.save_piece(htypes.layered_config_sheet.lcs_storage(rec_list))

    def _set(self, dir, record):
        self._dir_to_record[frozenset(dir)] = record

    def add(self, dir, piece, persist=False):
        log.info("LCS: add%s %s -> %s", '/persist' if persist else '', set(dir), piece)
        try:
            record = self._dir_to_record[frozenset(dir)]
        except KeyError:
            record = Record([piece], is_multi_value=True, persist=persist)
            self._dir_to_record[frozenset(dir)] = record
        else:
            if not record.is_multi_value:
                raise RuntimeError(f"LCS: Attempt to add value to single-value record: {set(dir)} -> {piece}")
            if record.persist != persist:
                raise RuntimeError(f"LCS: Attempt to change persistentency for: {set(dir)} -> {persist}")
            record.value_list.append(piece)
        if persist:
            self._save()

    def set(self, dir, piece, persist=False):
        log.info("LCS: set%s %s -> %s", '/persist' if persist else '', set(dir), piece)
        try:
            record = self._dir_to_record[frozenset(dir)]
        except KeyError:
            record = Record([piece], is_multi_value=False, persist=persist)
            self._dir_to_record[frozenset(dir)] = record
        else:
            if record.is_multi_value:
                raise RuntimeError(f"LCS: Attempt to set value to multi-value record: {set(dir)} -> {piece}")
            if record.persist != persist:
                raise RuntimeError(f"LCS: Attempt to change persistentency for: {set(dir)} -> {persist}")
            record.value_list = [piece]
        if persist:
            self._save()

    def remove(self, dir):
        record = self._dir_to_record.pop(frozenset(dir))
        log.info("LCS: remove%s %s -> %s", '/persist' if record.persist else '', set(dir), record.value_list)
        if record.persist:
            self._save()

    def _iter(self, filter_dir=None):
        filter_dir_set = set(filter_dir or [])
        for dir, record in self._dir_to_record.items():
            if filter_dir_set <= dir:
                yield set(dir), record

    def iter(self, filter_dir=None):
        for dir, record in self._iter(filter_dir):
            yield (dir, record.value_list, record.persist)

    def iter_dir_list_values(self, dir_list):
        for dir in dir_list:
            try:
                record = self._dir_to_record[frozenset(dir)]
            except KeyError:
                pass
            else:
                if not record.is_multi_value:
                    raise RuntimeError(f"LCS: Attempt to iter over values for single-value record: {set(dir)}")
                yield from record.value_list

    def slice(self, prefix_dir):
        prefix_dir_set = set(prefix_dir)
        dir_to_record = {}
        for dir, record in self._dir_to_record.items():
            if prefix_dir_set <= dir:
                slice_dir = frozenset(dir - prefix_dir_set)
                dir_to_record[slice_dir] = record
        return LCSlice(dir_to_record)

    def aux_bundler_hook(self, ref, t, value):
        for dir, record in self._iter({value}):
            log.info("LCS bundle aux: %s -> %s", dir, record)
            yield self._mosaic.put(record.as_piece(dir, self._mosaic))

    def aux_unbundler_hook(self, ref, t, value):
        if t is not htypes.layered_config_sheet.lcs_association:
            return
        dir, record = Record.from_piece(value, self._web, persist=False)
        try:
            prev_record = self._dir_to_record[frozenset(dir)]
        except KeyError:
            self._dir_to_record[frozenset(dir)] = record
            log.info("LCS unbundle aux: %s -> %s", set(dir), record)
        else:
            if record.is_multi_value != prev_record.is_multi_value:
                raise RuntimeError(f"LCS unbundle aux: Attempt to change is_multi_value for: {set(dir)}")
            log.debug("LCS unbundle aux: Warning: overriding %s: %s -> %s",  set(dir), prev_record, record)
            self._dir_to_record[frozenset(dir)] = record


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        bundle = services.file_bundle(lcs_path, encoding='cdr')
        lcs = LCSheet(services.mosaic, services.web, bundle)
        services.lcs = lcs
        services.aux_bundler_hooks.append(lcs.aux_bundler_hook)
        services.aux_unbundler_hooks.append(lcs.aux_unbundler_hook)
