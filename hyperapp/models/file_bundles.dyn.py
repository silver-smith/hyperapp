from pathlib import Path

from hyperapp.common import dict_coders  # register codec

from . import htypes
from .services import (
    file_bundle,
    )


def open_file_bundle_list():
    return htypes.file_bundles.bundle_list()


def file_bundle_list(piece):
    return [
        htypes.file_bundles.bundle_item("lcs", "~/.local/share/hyperapp/client/lcs.cdr"),
        htypes.file_bundles.bundle_item("client state", "~/.local/share/hyperapp/client/state.json"),
        ]


def open(piece, current_item):
    path = Path(current_item.path).expanduser()
    if path.suffix == '.json':
        encoding = 'json'
    elif path.suffix == '.cdr':
        encoding = 'cdr'
    else:
        raise RuntimeError(f"Unknown file bundle encoding suffix: {path.suffix!r}")
    bundle = file_bundle(path, encoding)
    piece_ref = bundle.load_ref()
    return htypes.data_browser.data_browser(
        data=piece_ref,
        )
