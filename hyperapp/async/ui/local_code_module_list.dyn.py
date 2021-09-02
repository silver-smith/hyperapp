from collections import namedtuple

from . import htypes
from .command import command
from .column import Column
from .simple_list_object import SimpleListObject
from .module import ClientModule


Item = namedtuple('Item', 'module_name module_ref file_path')


class LocalCodeModuleList(SimpleListObject):

    dir_list = [
        *SimpleListObject.dir_list,
        [htypes.local_code_module_list.local_code_module_list_d()],
        ]

    @classmethod
    async def from_piece(cls, piece, local_code_module_registry, async_web):
        self = cls()
        await self._async_init(local_code_module_registry, async_web)
        return self
        
    def __init__(self):
        super().__init__()
        self._name_to_item = None

    async def _async_init(self, local_code_module_registry, async_web):
        self._name_to_item = {}
        for module_name, rec in local_code_module_registry.items():
            module = await async_web.summon(rec.module_ref)
            self._name_to_item[module_name] = Item(module_name, rec.module_ref, module.file_path)

    @property
    def piece(self):
        return htypes.local_code_module_list.local_code_module_list()

    @property
    def title(self):
        return f"Local code modules"

    @property
    def columns(self):
        return [
            Column('module_name', is_key=True),
            Column('file_path'),
            ]

    async def get_all_items(self):
        return list(self._name_to_item.values())

    @command
    async def open(self, current_key):
        item = self._name_to_item[current_key]
        return htypes.data_viewer.data_viewer(item.module_ref)


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.object_registry.register_actor(
            htypes.local_code_module_list.local_code_module_list,
            LocalCodeModuleList.from_piece,
            services.local_code_module_registry,
            services.async_web,
            )

    @command
    async def local_code_module_list(self):
        return htypes.local_code_module_list.local_code_module_list()
