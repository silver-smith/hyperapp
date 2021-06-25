import logging
from collections import defaultdict
from pathlib import Path

from . import htypes
from .module import ClientModule

log = logging.getLogger(__name__)


lcs_path = Path('~/.local/share/hyperapp/client/lcs.cdr').expanduser()


class LCSheet:

    def __init__(self, mosaic, web, bundle):
        self._mosaic = mosaic
        self._bundle = bundle
        self._dir_to_value_list = defaultdict(list)
        try:
            storage = bundle.load_piece()
        except FileNotFoundError:
            pass
        else:
            for rec in storage.record_list:
                value = web.summon(rec.value_ref)
                log.info("LCS: loaded %s -> %s", rec.dir, value)
                self._add(rec.dir, value)

    def _save(self):
        rec_list = []
        for dir, value_list in self._dir_to_value_list.items():
            for value in value_list:
                rec = htypes.layered_config_sheet.lcs_record(
                    dir=dir,
                    value_ref=self._mosaic.put(value),
                    )
                rec_list.append(rec)
        self._bundle.save_piece(htypes.layered_config_sheet.lcs_storage(rec_list))

    def _add(self, dir, piece):
        self._dir_to_value_list[tuple(dir)].append(piece)

    def add(self, dir, piece):
        log.info("LCS: add %s -> %s", dir, piece)
        self._add(dir, piece)
        self._save()

    def set(self, dir, piece):
        log.info("LCS: set %s -> %s", dir, piece)
        self._dir_to_value_list[tuple(dir)] = [piece]
        self._save()

    def iter(self, dir_list):
        for dir in dir_list:
            yield from self._dir_to_value_list[tuple(dir)]

    def get(self, dir):
        piece_list = self._dir_to_value_list[tuple(dir)]
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
