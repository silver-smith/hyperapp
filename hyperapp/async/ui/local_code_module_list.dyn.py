from collections import namedtuple

from . import htypes
from .command import command
from .simple_list_object import SimpleListObject
from .module import ClientModule


Item = namedtuple('Item', 'module_name module_ref file_path')


class LocalCodeModuleList(SimpleListObject):

    dir_list = [
        *SimpleListObject.dir_list,
        [htypes.local_code_module_list.local_code_module_list_d()],
        ]

    @classmethod
    async def from_piece(cls, piece, module_registry, mosaic, async_web):
        self = cls()
        await self._async_init(module_registry, mosaic, async_web)
        return self
        
    def __init__(self):
        super().__init__()
        self._name_to_item = None

    async def _async_init(self, module_registry, mosaic, async_web):
        self._name_to_item = {}
        for rec in module_registry.elements():
            module_ref = mosaic.put(rec.module)
            self._name_to_item[rec.name] = Item(rec.name, module_ref, rec.module.file_path)

    @property
    def piece(self):
        return htypes.local_code_module_list.local_code_module_list()

    @property
    def title(self):
        return f"Local code modules"

    @property
    def key_attribute(self):
        return 'module_name'

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
            services.module_registry,
            services.mosaic,
            services.async_web,
            )

    @command
    async def local_code_module_list(self):
        return htypes.local_code_module_list.local_code_module_list()
