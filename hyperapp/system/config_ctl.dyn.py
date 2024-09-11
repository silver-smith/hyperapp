from abc import ABCMeta, abstractmethod

from . import htypes


class ConfigCtl(metaclass=ABCMeta):

    @abstractmethod
    def from_data(self, piece):
        pass

    # @abstractmethod
    # def to_data(self, config_template):
    #     pass

    @abstractmethod
    def merge(self, dest, src):
        pass

    @abstractmethod
    def resolve(self, config_template):
        pass


class DictConfigCtl(ConfigCtl):

    def merge(self, dest, src):
        dest.update(src)

    def resolve(self, system, service_name, config_template):
        config = {}
        for key, value_template in config_template.items():
            config[key] = value_template.resolve(system, service_name)
        return config


class ItemDictConfigCtl(DictConfigCtl):

    @classmethod
    def from_piece(cls, piece, cfg_item_creg):
        return cls(cfg_item_creg)

    def __init__(self, cfg_item_creg):
        self._cfg_item_creg = cfg_item_creg

    @property
    def piece(self):
        return htypes.system.item_dict_config_ctl()

    def from_data(self, piece):
        config = {}
        for item_ref in piece.items:
            template = self._cfg_item_creg.invite(item_ref)
            config[template.key] = template
        return config

    def item_piece(self, template):
        return self._cfg_item_creg.actor_to_piece(template)


# class ServiceConfigCtl(ItemDictConfigCtl):
#     pass


# class ActorConfigCtl(ItemDictConfigCtl):
#     pass
