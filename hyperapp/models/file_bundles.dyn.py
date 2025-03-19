from pathlib import Path

from hyperapp.boot import dict_coders  # register codec

from . import htypes
from .code.mark import mark


@mark.global_command
def open_file_bundle_list():
    return htypes.file_bundles.view()


@mark.model
def file_bundle_list(piece):
    return [
        htypes.file_bundles.item("Client state", "~/.local/share/hyperapp/client/layout.json"),
        htypes.file_bundles.item("Peer list", "~/.local/share/hyperapp/client/peer_list.json"),
        htypes.file_bundles.item("lcs", "~/.local/share/hyperapp/client/lcs.cdr"),
        ]


@mark.command
def open(piece, current_item, file_bundle_factory):
    path = Path(current_item.path).expanduser()
    if path.suffix == '.json':
        encoding = 'json'
    elif path.suffix == '.cdr':
        encoding = 'cdr'
    else:
        raise RuntimeError(f"Unknown file bundle encoding suffix: {path.suffix!r}")
    bundle = file_bundle_factory(path, encoding)
    piece_ref = bundle.load_ref(register_associations=False)
    return htypes.data_browser.record_view(
        data=piece_ref,
        )
