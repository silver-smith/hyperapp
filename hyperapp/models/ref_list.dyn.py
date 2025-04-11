import uuid
from collections import namedtuple
from pathlib import Path

from hyperapp.boot.htypes.packet_coders import packet_coders

from . import htypes
from .services import (
    web,
    )
from .code.mark import mark


_STORAGE_PATH = Path.home() / '.local/share/hyperapp/server/ref_list.yaml'


class RefList:

    # _Folder = namedtuple('RefList._Folder', 'id parent_id name')
    # _Ref = namedtuple('RefList._Ref', 'id parent_id ref')

    def __init__(self, storage_path):
        self._storage_path = storage_path
        self._folders = []
        self._refs = []
        self._loaded = False

    def enum_items(self, format, parent_id=None):
        self._ensure_loaded()
        for folder in self._folders:
            if folder.parent_id != parent_id:
                continue
            yield htypes.ref_list.item(
                id=folder.id,
                name=folder.name,
                )
        for ref in self._refs:
            if ref.parent_id != parent_id:
                continue
            piece = web.summon(ref.ref)
            name = format(piece)
            yield htypes.ref_list.item(
                id=ref.id,
                name=name,
                )

    def append_folder(self, parent_id, name):
        self._ensure_loaded()
        folder = htypes.ref_list.folder(
            id=str(uuid.uuid4()),
            parent_id=parent_id,
            name=name,
            )
        self._folders.append(folder)
        self._save()
        return folder.id

    def _ensure_loaded(self):
        if not self._loaded:
            self._read()
            self._loaded = True

    def _read(self):
        try:
            yaml_data = self._storage_path.read_bytes()
        except FileNotFoundError:
            return
        storage = packet_coders.decode('yaml', yaml_data, htypes.ref_list.storage)
        self._folders = list(storage.folders)
        self._refs = list(storage.refs)
        # for folder in storage.folders:
        #     self._folders.append(folder)
        #         self._Folder(folder.id, folder.parent_id, folder.name))
        # for ref in storage.refs:
        #     self._refs.append(
        #         self._Ref(folder.id, folder.parent_id, folder.name))

    def _save(self):
        storage = htypes.ref_list.storage(
            folders=tuple(self._folders),
            refs=tuple(self._refs),
            )
        yaml_data = packet_coders.encode('yaml', storage)
        self._storage_path.write_bytes(yaml_data)


def _get_ref_list():
    return RefList(_STORAGE_PATH)


@mark.model(key='id')
def ref_list_model(piece, format):
    ref_list = _get_ref_list()
    return list(ref_list.enum_items(format, piece.parent_id))


@mark.command(args=['name'])
def add_folder(piece, name):
    ref_list = _get_ref_list()
    folder_id = ref_list.append_folder(piece.parent_id, name)
    return (piece, folder_id)


@mark.global_command
def open_ref_list():
    return htypes.ref_list.model(parent_id=None)
