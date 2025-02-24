from . import htypes
from .code.mark import mark
from .code.config_ctl import MultiItemConfigCtl, DictConfigCtl


class DictListConfigCtl(DictConfigCtl):

    @classmethod
    @mark.actor.config_ctl_creg
    def from_piece(cls, piece, cfg_item_creg):
        return cls(cfg_item_creg)

    @property
    def piece(self):
        return htypes.list_config_ctl.dict_list_config_ctl()

    def _config_to_items(self, config):
        items = []
        for key, values in config.items():
            items += values
        return items

    def merge(self, dest, src):
        for key, value_list in src.items():
            dest.setdefault(key, []).extend(value_list)

    def _update_config(self, config_template, item):
        config_template.setdefault(item.key, []).append(item)

    def resolve_item(self, system, service_name, item):
        return [
            item_template.resolve(system, service_name)
            for item_template in item
            ]


class FlatListConfigCtl(MultiItemConfigCtl):

    @classmethod
    @mark.actor.config_ctl_creg
    def from_piece(cls, piece, cfg_item_creg):
        return cls(cfg_item_creg)

    @property
    def piece(self):
        return htypes.list_config_ctl.flat_list_config_ctl()

    def _config_to_items(self, config):
        return config

    def empty_config_template(self):
        return []

    def _update_config(self, config_template, item):
        config_template.append(item)

    def merge(self, dest, src):
        dest.extend(src)

    def _lazy_config(self, system, service_name, config_template):
        assert False, "TODO"

    def resolve(self, system, service_name, config_template):
        config = []  # command list.
        for item in config_template:
            value = item.resolve(system, service_name)
            config.append(value)
        return config
