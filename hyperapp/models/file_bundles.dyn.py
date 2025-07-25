from pathlib import Path

from hyperapp.boot.ref import make_ref
from hyperapp.boot import dict_coders  # register codec

from . import htypes
from .code.mark import mark


@mark.global_command
def open_file_bundle_list():
    return htypes.file_bundles.view()


@mark.model
def file_bundle_list(piece):
    return [
        htypes.file_bundles.item("Server config", "~/.local/share/hyperapp/server/config.cdr"),
        htypes.file_bundles.item("Client config", "~/.local/share/hyperapp/client/config.cdr"),
        htypes.file_bundles.item("Client state", "~/.local/share/hyperapp/client/layout.json"),
        htypes.file_bundles.item("Peer list", "~/.local/share/hyperapp/client/peer_list.json"),
        htypes.file_bundles.item("Server peer", "~/.local/share/hyperapp/server/peer.json"),
        htypes.file_bundles.item("Server identity", "~/.local/share/hyperapp/server/identity.json"),
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
    file_bundle = file_bundle_factory(path, encoding)
    bundle = file_bundle.load(register_associations=False)
    return htypes.bundle_info.model(
        bundle_name=current_item.name,
        roots=bundle.roots,
        associations=bundle.associations,
        capsules=tuple(make_ref(capsule) for capsule in bundle.capsule_list),
        )
