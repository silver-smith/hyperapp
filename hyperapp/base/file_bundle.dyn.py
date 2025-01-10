import logging
from functools import partial

from hyperapp.boot.htypes import bundle_t
from hyperapp.boot.htypes.packet_coders import packet_coders

from .services import (
    mosaic,
    unbundler,
    )
from .code.mark import mark

log = logging.getLogger(__name__)


DEFAULT_ENCODING = 'json'


class FileBundle:

    def __init__(self, bundler, path, encoding):
        self._bundler = bundler
        self.path = path
        self._encoding = encoding

    def save_ref(self, ref):
        bundle = self._bundler([ref]).bundle
        data = packet_coders.encode(self._encoding, bundle, bundle_t)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_bytes(data)
        log.info("Saved %s to %s (%d bytes)", ref, self.path, len(data))

    def load_ref(self, register_associations=True):
        bundle = packet_coders.decode(self._encoding, self.path.read_bytes(), bundle_t)
        unbundler.register_bundle(bundle, register_associations)
        ref_count = len(bundle.roots)
        if ref_count != 1:
            raise RuntimeError(f"Bundle {self.path} has {ref_count} refs, but expected only one")
        return bundle.roots[0]

    def save_piece(self, piece):
        log.info("Save %s to %s", piece, self.path)
        ref = mosaic.put(piece)
        self.save_ref(ref)

    def load_piece(self, register_associations=True):
        ref = self.load_ref(register_associations)
        return mosaic.resolve_ref(ref).value


@mark.service
def file_bundle(bundler, path, encoding=DEFAULT_ENCODING):
    return FileBundle(bundler, path, encoding)
