from . import htypes
from .code.mark import mark
from .code.config_ctl import ConfigCtl


class CommandConfigCtl(ConfigCtl):

    @classmethod
    @mark.actor.config_ctl_creg  #(htypes.command.config_ctl)
    def from_piece(cls, piece, cfg_item_creg):
        return cls(cfg_item_creg)

    def __init__(self, cfg_item_creg=None):
        self._cfg_item_creg = cfg_item_creg

    @property
    def piece(self):
        return htypes.command.config_ctl()

    def merge(self, dest, src):
        for key, value_list in src.items():
            dest.setdefault(key, []).extend(value_list)

    def from_data(self, piece):
        config = {}
        for item_ref in piece.items:
            template = self._cfg_item_creg.invite(item_ref)
            config.setdefault(template.key, []).append(template)
        return config

    def resolve(self, system, service_name, config_template):
        config = {}
        for key, value_template_list in config_template.items():
            for value_template in value_template_list:
                value = value_template.resolve(system, service_name)
                config.setdefault(key, []).append(value)
        return config

    def item_piece(self, template):
        return self._cfg_item_creg.actor_to_piece(template)

    def items_to_data(self, item_list):
        return htypes.command.item_list_config(
            items=tuple(
                mosaic.put(item)
                for item in item_list
                ),
            )
