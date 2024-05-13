import logging
from dataclasses import dataclass, field
from typing import Any

from . import htypes
from .services import (
    mosaic,
    web,
    )

log = logging.getLogger(__name__)


@dataclass
class SingleRecord:
    value: Any
    persist: bool = False

    def association_list(self, dir):
        dir_refs = tuple(
            mosaic.put(element)
            for element in dir
            )
        values_ref = mosaic.put(self.value)
        return [htypes.lcs.lcs_association(dir_refs, values_ref)]

    @property
    def value_set(self):
        return {self.value}


@dataclass
class MultiRecord:
    value_set: set = field(default_factory=set)
    persist: bool = False

    def association_list(self, dir):
        dir_refs = tuple(
            mosaic.put(element)
            for element in dir
            )
        return [
            htypes.lcs.lcs_set_association(dir_refs, mosaic.put(value))
            for value in self.value_set
            ]


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
        if not isinstance(record, SingleRecord):
            raise RuntimeError(f"LCS: Attempt to get single value from multi-value record: {set(dir)}")
        [value] = record.value_set
        return value


class LCSheet(LCSlice):

    def __init__(self, bundle=None):
        super().__init__()
        self._bundle = bundle
        self._load()

    def _load(self):
        if not self._bundle:
            return
        try:
            storage = self._bundle.load_piece(register_associations=False)
        except FileNotFoundError:
            pass
        else:
            for association_ref in storage.association_list:
                association = web.summon(association_ref)
                dir, record = self._add_association(association, persist=True)
                log.info("LCS: loaded %s -> %s", set(dir), record)

    def _save(self):
        if not self._bundle:
            return
        association_list = []
        for dir, record in self._dir_to_record.items():
            if not record.persist:
                continue
            association_list += [
                mosaic.put(piece)
                for piece in record.association_list(dir)
                ]
        self._bundle.save_piece(htypes.lcs.storage(tuple(association_list)))

    def register_association(self, association):
        self._add_association(association, persist=False)

    def _add_association(self, association, persist):
        dir = [
            web.summon(ref)
            for ref in association.dir
            ]
        value = web.summon(association.value)
        if isinstance(association, htypes.lcs.lcs_association):
            record = self._set(dir, value, persist)
        else:
            assert isinstance(association, htypes.lcs.lcs_set_association)
            record = self._add(dir, value, persist)
        return (dir, record)

    def _set(self, dir, piece, persist):
        fs_dir = frozenset(dir)
        try:
            record = self._dir_to_record[fs_dir]
        except KeyError:
            record = SingleRecord(piece, persist)
            self._dir_to_record[fs_dir] = record
        else:
            if not isinstance(record, SingleRecord):
                raise RuntimeError(f"LCS: Attempt to set value to multi-value record: {set(dir)} -> {piece}")
            if record.persist != persist:
                raise RuntimeError(f"LCS: Attempt to change persistentency for: {set(dir)} -> {persist}")
            record.value = piece
        return record

    def _add(self, dir, piece, persist):
        fs_dir = frozenset(dir)
        try:
            record = self._dir_to_record[fs_dir]
        except KeyError:
            record = MultiRecord({piece}, persist)
            self._dir_to_record[fs_dir] = record
        else:
            if not isinstance(record, MultiRecord):
                raise RuntimeError(f"LCS: Attempt to add value to single-value record: {set(dir)} -> {piece}")
            if record.persist != persist:
                raise RuntimeError(f"LCS: Attempt to change persistentency for: {set(dir)} -> {persist}")
            record.value_set.add(piece)
        return record

    def add(self, dir, piece, persist=False):
        log.info("LCS: add%s %s -> %s", '/persist' if persist else '', set(dir), piece)
        self._add(dir, piece, persist)
        if persist:
            self._save()

    def set(self, dir, piece, persist=False):
        log.info("LCS: set%s %s -> %s", '/persist' if persist else '', set(dir), piece)
        self._set(dir, piece, persist)
        if persist:
            self._save()

    def remove(self, dir):
        record = self._dir_to_record.pop(frozenset(dir))
        log.info("LCS: remove%s %s -> %s", '/persist' if record.persist else '', set(dir), record)
        if record.persist:
            self._save()

    def _iter(self, filter_dir=None):
        filter_dir_set = set(filter_dir or [])
        for dir, record in self._dir_to_record.items():
            if filter_dir_set <= dir:
                yield set(dir), record

    def iter(self, filter_dir=None):
        for dir, record in self._iter(filter_dir):
            yield (dir, record.value_set, record.persist)

    def iter_dir_list_values(self, dir_list):
        for dir in dir_list:
            try:
                record = self._dir_to_record[frozenset(dir)]
            except KeyError:
                pass
            else:
                if not isinstance(record, MultiRecord):
                    raise RuntimeError(f"LCS: Attempt to iter over values for single-value record: {set(dir)}")
                yield from record.value_set

    def slice(self, prefix_dir):
        prefix_dir_set = set(prefix_dir)
        dir_to_record = {}
        for dir, record in self._dir_to_record.items():
            if prefix_dir_set <= dir:
                slice_dir = frozenset(dir - prefix_dir_set)
                dir_to_record[slice_dir] = record
        return LCSlice(dir_to_record)
