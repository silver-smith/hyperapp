from . import htypes
from .code.mark import mark
from .code.config_ctl import MultiItemConfigCtl, DictConfigCtl


class TypedCommandConfigCtl(DictConfigCtl):

    @classmethod
    @mark.actor.config_ctl_creg
    def from_piece(cls, piece, cfg_item_creg):
        return cls(cfg_item_creg)

    @property
    def piece(self):
        return htypes.command.typed_config_ctl()

    def merge(self, dest, src):
        for key, value_list in src.items():
            dest.setdefault(key, []).extend(value_list)

    def update_config(self, config_template, item):
        config_template.setdefault(item.key, []).append(item)

    def resolve_item(self, system, service_name, item):
        return [
            item_template.resolve(system, service_name)
            for item_template in item
            ]


class UntypedCommandConfigCtl(MultiItemConfigCtl):

    @classmethod
    @mark.actor.config_ctl_creg
    def from_piece(cls, piece, cfg_item_creg):
        return cls(cfg_item_creg)

    @property
    def piece(self):
        return htypes.command.untyped_config_ctl()

    def empty_config_template(self):
        return []

    def update_config(self, config_template, item):
        config_template.append(item)

    def merge(self, dest, src):
        dest.extend(src)

    def lazy_config(self, system, service_name, config_template):
        assert False, "TODO"

    def resolve(self, system, service_name, config_template):
        config = []  # command list.
        for item in config_template:
            value = item.resolve(system, service_name)
            config.append(value)
        return config
