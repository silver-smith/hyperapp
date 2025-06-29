from . import htypes
from .services import (
    mosaic,
    )
from .code.config_ctl import DictConfigCtl


class DictListConfigCtl(DictConfigCtl):

    @property
    def piece(self):
        return htypes.list_config_ctl.dict_list_config_ctl(
            value_ctl=mosaic.put(self._value_ctl.piece),
            )

    @staticmethod
    def config_to_items(config_template):
        items = []
        for key, value_list in config_template.items():
            for value in value_list:
                items.append((key, value))
        return items

    def merge(self, dest, src):
        for key, value_list in src.items():
            dest.setdefault(key, []).extend(value_list)
        return dest

    def _update_config(self, config_template, key, item):
        config_template.setdefault(key, []).append(item)

    def resolve_value(self, system, service_name, key, template):
        return [
            self._value_ctl.resolve(elt, key, system, service_name)
            for elt in template
            ]
