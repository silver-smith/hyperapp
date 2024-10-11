from abc import ABCMeta, abstractmethod

from . import htypes


class ConfigCtl(metaclass=ABCMeta):

    @abstractmethod
    def from_data(self, piece):
        pass

    @abstractmethod
    def merge(self, dest, src):
        pass

    @abstractmethod
    def lazy_config(self, system, service_name, config_template):
        pass

    @abstractmethod
    def resolve(self, system, service_name, config_template):
        pass


class LazyDictConfig:

    def __init__(self, ctl, system, service_name, config_template):
        self._ctl = ctl
        self._system = system
        self._service_name = service_name
        self._config_template = config_template  # key -> template
        self._resolved_config = {}

    def __getitem__(self, key):
        try:
            return self._resolved_config[key]
        except KeyError:
            pass
        value_template = self._config_template[key]  # KeyError is raised from here.
        value = self._ctl.resolve_item(self._system, self._service_name, value_template)
        self._resolved_config[key] = value
        return value

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default


class DictConfigCtl(ConfigCtl):

    def merge(self, dest, src):
        dest.update(src)

    def lazy_config(self, system, service_name, config_template):
        return LazyDictConfig(self, system, service_name, config_template)

    def resolve(self, system, service_name, config_template):
        config = {}
        for key, value_template in config_template.items():
            config[key] = self.resolve_item(system, service_name, value_template)
        return config

    def resolve_item(self, system, service_name, value_template):
        return value_template.resolve(system, service_name)


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
