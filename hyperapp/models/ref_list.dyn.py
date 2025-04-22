import logging
import uuid
from collections import defaultdict, namedtuple
from pathlib import Path

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.mark import mark

log = logging.getLogger(__name__)

_STORAGE_PATH = Path.home() / '.local/share/hyperapp/server/ref_list.cdr'


class RefList:

    def __init__(self, file_bundle):
        self._file_bundle = file_bundle
        self._folders = {}
        self._refs = {}
        self._folder_has_names = defaultdict(set)
        self._folder_has_refs = defaultdict(set)
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

    def remove(self, item_id):
        self._ensure_loaded()
        try:
            folder = self._folders[item_id]
            del self._folders[item_id]
            self._folder_has_names[folder.parent_id].remove(folder.name)
        except KeyError:
            ref = self._refs[item_id]
            del self._refs[item_id]
            self._folder_has_refs[ref.parent_id].remove(ref.ref)
        self._save()

    def append_folder(self, parent_id, name):
        self._ensure_loaded()
        if name in self._folder_has_names[parent_id]:
            log.warning("Folder with name %r already exists", name)
            return None
        folder = htypes.ref_list.folder(
            id=str(uuid.uuid4()),
            parent_id=parent_id,
            name=name,
            )
        self._folders[folder.id] = folder
        self._folder_has_names[parent_id].add(name)
        self._save()
        return folder.id

    def append_ref(self, parent_id, ref):
        self._ensure_loaded()
        if ref in self._folder_has_refs[parent_id]:
            log.warning("Ref %s already exists", ref)
            return None
        ref_item = htypes.ref_list.ref(
            id=str(uuid.uuid4()),
            parent_id=parent_id,
            ref=ref,
            )
        self._refs[ref_item.id] = ref_item
        self._folder_has_refs[parent_id].add(ref)
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
        for folder in self._folders.values():
            self._folder_has_names[folder.parent_id].add(folder.name)
        for ref in self._refs.values():
            self._folder_has_refs[ref.parent_id].add(ref.ref)

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
def open(piece, current_key, request, ref_list):
    try:
        folder = ref_list.get_folder(current_key)
        path = [folder.name]
        while folder.parent_id:
            folder = ref_list.get_folder(folder.parent_id)
            path = [folder.name, *path]
        piece = htypes.ref_list.model(
            parent_id=current_key,
            folder_path=tuple(path),
            )
        if request:
            piece = htypes.model.remote_model(
                model=mosaic.put(piece),
                remote_peer=mosaic.put(request.receiver_identity.peer.piece),
                )
        return piece
    except KeyError:
        ref = ref_list.get_ref(current_key)
        return web.summon(ref.ref)


@mark.command
def open_parent(piece, request, ref_list):
    if not piece.parent_id:
        return
    folder = ref_list.get_folder(piece.parent_id)
    piece = htypes.ref_list.model(
        parent_id=folder.parent_id,
        folder_path=piece.folder_path[:-1],
        )
    if request:
        piece = htypes.model.remote_model(
            model=mosaic.put(piece),
            remote_peer=mosaic.put(request.receiver_identity.peer.piece),
            )
    return (piece, folder.id)


@mark.command.add(args=['name'])
def add_folder(piece, name, ref_list):
    folder_id = ref_list.append_folder(piece.parent_id, name)
    return folder_id


@mark.command.add(args=['ref'])
def add_ref(piece, ref, ref_list):
    ref_id = ref_list.append_ref(piece.parent_id, ref)
    return ref_id


@mark.command.remove
def remove(piece, current_id, ref_list):
    ref_list.remove(current_id)
    return True


@mark.global_command
def open_ref_list():
    return htypes.ref_list.model(parent_id=None, folder_path=())


@mark.actor.formatter_creg
def format_model(piece):
    path = "/"
    for name in piece.folder_path:
        path += name + "/"
    return f"Ref list: {path}"
