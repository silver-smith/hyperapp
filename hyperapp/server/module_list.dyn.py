import logging
from functools import cached_property

from . import htypes
from .services import (
    local_modules,
    mark,
    module_registry,
    mosaic,
    web,
    )

log = logging.getLogger(__name__)


class ModuleList:

    def __init__(self, piece):
        self._status_filter = piece.status

    # Should be populated only after all modules are imported, otherwise not-yet imported modules are shown as available.
    @cached_property
    def _name_to_item(self):
        name_to_item = {}
        imported_names = {rec.name for rec in module_registry.elements()}
        for module_name, module in local_modules.by_name.items():
            module_ref = mosaic.put(module)
            if module_name in imported_names:
                status = 'imported'
            else:
                status = 'available'
            name_to_item[module_name] = htypes.module_list.item(
                module_name,
                module_ref,
                module.file_path,
                status,
                )
        return name_to_item

    def get(self):
        log.info("ModuleList(%s).list", self._status_filter)
        return list(
            item for item
            in self._name_to_item.values()
            if (not self._status_filter
                or item.status in self._status_filter)
            )

    def open(self, current_key):
        item = self._name_to_item[current_key]
        return web.summon(item.module_ref)


@mark.global_command
def open_module_list():
    return htypes.module_list.module_list(status=None)


@mark.global_command
def open_imported_module_list():
    return htypes.module_list.module_list(status='imported')


@mark.global_command
def open_available_module_list():
    return htypes.module_list.module_list(status='available')
