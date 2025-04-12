import uuid
from collections import namedtuple
from pathlib import Path

from . import htypes
from .services import (
    web,
    )
from .code.mark import mark


_STORAGE_PATH = Path.home() / '.local/share/hyperapp/server/ref_list.cdr'


class RefList:

    def __init__(self, file_bundle):
        self._file_bundle = file_bundle
        self._folders = {}
        self._refs = {}
        self._loaded = False

    def enum_items(self, format, parent_id=None):
        self._ensure_loaded()
        for folder in self._folders.values():
            if folder.parent_id != parent_id:
                continue
            yield htypes.ref_list.item(
                id=folder.id,
                name=folder.name,
                )
        for ref in self._refs.values():
            if ref.parent_id != parent_id:
                continue
            piece = web.summon(ref.ref)
            name = format(piece)
            yield htypes.ref_list.item(
                id=ref.id,
                name=name,
                )

    def get_folder(self, item_id):
        self._ensure_loaded()
        return self._folders[item_id]

    def get_ref(self, item_id):
        self._ensure_loaded()
        return self._refs[item_id]

    def append_folder(self, parent_id, name):
        self._ensure_loaded()
        folder = htypes.ref_list.folder(
            id=str(uuid.uuid4()),
            parent_id=parent_id,
            name=name,
            )
        self._folders[folder.id] = folder
        self._save()
        return folder.id

    def append_ref(self, parent_id, ref):
        self._ensure_loaded()
        ref_item = htypes.ref_list.ref(
            id=str(uuid.uuid4()),
            parent_id=parent_id,
            ref=ref,
            )
        self._refs[ref_item.id] = ref_item
        self._save()
        return ref_item.id

    def _ensure_loaded(self):
        if not self._loaded:
            self._read()
            self._loaded = True

    def _read(self):
        try:
            storage = self._file_bundle.load_piece()
        except FileNotFoundError:
            return
        self._folders = {folder.id: folder for folder in storage.folders}
        self._refs = {ref.id: ref for ref in storage.refs}

    def _save(self):
        storage = htypes.ref_list.storage(
            folders=tuple(self._folders.values()),
            refs=tuple(self._refs.values()),
            )
        self._file_bundle.save_piece(storage)


@mark.service
def ref_list(file_bundle_factory):
    file_bundle = file_bundle_factory(_STORAGE_PATH, encoding='cdr')
    return RefList(file_bundle)


@mark.model(key='id')
def ref_list_model(piece, format, ref_list):
    return list(ref_list.enum_items(format, piece.parent_id))


@mark.command
def open(piece, current_key, ref_list):
    try:
        folder = ref_list.get_folder(current_key)
        path = [folder.name]
        while folder.parent_id:
            folder = ref_list.get_folder(folder.parent_id)
            path = [folder.name, *path]
        return htypes.ref_list.model(
            parent_id=current_key,
            folder_path=tuple(path),
            )
    except KeyError:
        ref = ref_list.get_ref(current_key)
        return web.summon(ref.ref)


@mark.command
def open_parent(piece, ref_list):
    if not piece.parent_id:
        return
    folder = ref_list.get_folder(piece.parent_id)
    piece = htypes.ref_list.model(
        parent_id=folder.parent_id,
        folder_path=piece.folder_path[:-1],
        )
    return (piece, folder.id)


@mark.command(args=['name'])
def add_folder(piece, name, ref_list):
    folder_id = ref_list.append_folder(piece.parent_id, name)
    return (piece, folder_id)


@mark.command(args=['ref'])
def add_ref(piece, ref, ref_list):
    ref_id = ref_list.append_ref(piece.parent_id, ref)
    return (piece, ref_id)


@mark.global_command
def open_ref_list():
    return htypes.ref_list.model(parent_id=None, folder_path=())


@mark.actor.formatter_creg
def format_model(piece):
    path = "/"
    for name in piece.folder_path:
        path += name + "/"
    return f"Ref list: {path}"
