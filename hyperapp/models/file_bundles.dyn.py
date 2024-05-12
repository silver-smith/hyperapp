from . import htypes


def file_bundle_list(piece):
    return [
        htypes.file_bundles.bundle("lcs", "~/.local/share/hyperapp/client/lcs.cdr"),
        htypes.file_bundles.bundle("client state", "~/.local/share/hyperapp/client/state.json"),
        ]


def open_file_bundle_list():
    return htypes.file_bundles.bundle_list()
