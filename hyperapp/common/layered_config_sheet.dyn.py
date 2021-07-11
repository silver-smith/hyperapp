import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List
from pathlib import Path

from . import htypes
from .module import ClientModule

log = logging.getLogger(__name__)


lcs_path = Path('~/.local/share/hyperapp/client/lcs.cdr').expanduser()


@dataclass
class Record:
    persist = False
    value_list: List = field(default_factory=list)
    

class LCSheet:

    def __init__(self, mosaic, web, bundle):
        self._mosaic = mosaic
        self._web = web
        self._bundle = bundle
        self._dir_to_record = defaultdict(Record)
        self._load()

    def _load(self):
        try:
            storage = self._bundle.load_piece()
        except FileNotFoundError:
            pass
        else:
            for rec in storage.record_list:
                dir = [
                    self._web.summon(ref)
                    for ref in rec.dir
                    ]
                value = self._web.summon(rec.value_ref)
                log.info("LCS: loaded %s -> %s", dir, value)
                record = self._add(dir, value)
                record.persist = True

    def _save(self):
        rec_list = []
        for dir, record in self._dir_to_record.items():
            if not record.persist:
                continue
            dir_refs = [
                self._mosaic.put(element)
                for element in dir
                ]
            for value in record.value_list:
                rec = htypes.layered_config_sheet.lcs_record(
                    dir=dir_refs,
                    value_ref=self._mosaic.put(value),
                    )
                rec_list.append(rec)
        self._bundle.save_piece(htypes.layered_config_sheet.lcs_storage(rec_list))

    def _add(self, dir, piece):
        record = self._dir_to_record[tuple(dir)]
        record.value_list.append(piece)
        return record

    def add(self, dir, piece, persist=False):
        log.info("LCS: add%s %s -> %s", '/persist' if persist else '', dir, piece)
        record = self._add(dir, piece)
        if persist:
            record.persist = True
            self._save()

    def set(self, dir, piece, persist=False):
        log.info("LCS: set%s %s -> %s", '/persist' if persist else '', dir, piece)
        record = self._dir_to_record[tuple(dir)]
        record.value_list = [piece]
        if persist:
            record.persist = True
            self._save()

    def remove(self, dir):
        record = self._dir_to_record[tuple(dir)]
        log.info("LCS: remove%s %s -> %s", '/persist' if record.persist else '', dir, record.value_list)
        del self._dir_to_record[tuple(dir)]
        if record.persist:
            self._save()

    def iter(self, dir_list):
        for dir in dir_list:
            yield from self._dir_to_record[tuple(dir)].value_list

    def get(self, dir):
        try:
            piece_list = self._dir_to_record[tuple(dir)].value_list
        except TypeError as x:
            raise RuntimeError(f"Type error: {x}: {dir!r}")
        if len(piece_list) > 1:
            raise RuntimeError(f"More than one value is registered for {dir}")
        if piece_list:
            return piece_list[0]
        return None

    def get_first(self, dir_list):
        for dir in reversed(dir_list):
            value = self.get(dir)
            if value is not None:
                return value
        raise KeyError(f"No dir among {dir_list} is registered at LCS")


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        bundle = services.file_bundle(lcs_path, encoding='cdr')
        services.lcs = LCSheet(services.mosaic, services.web, bundle)
