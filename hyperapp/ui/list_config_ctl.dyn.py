from . import htypes
from .code.mark import mark
from .code.config_ctl import MultiItemConfigCtl, DictConfigCtl


class DictListConfigCtl(DictConfigCtl):

    @classmethod
    @mark.actor.config_ctl_creg
    def from_piece(cls, piece, cfg_item_creg, cfg_value_creg):
        return cls(cfg_item_creg, cfg_value_creg)

    @property
    def piece(self):
        return htypes.list_config_ctl.dict_list_config_ctl()

    @staticmethod
    def _config_to_items(config_template):
        items = []
        for values in config_template.values():
            items += values
        return items

    def merge(self, dest, src):
        for key, value_list in src.items():
            dest.setdefault(key, []).extend(value_list)
        return dest

    def _update_config(self, config_template, key, item):
        config_template.setdefault(key, []).append(item)

    def resolve_item(self, system, service_name, key, item):
        return [
            self._cfg_value_creg.animate(elt, key, system, service_name)
            for elt in item
            ]
