from abc import ABCMeta, abstractmethod

from . import htypes
from .services import (
    mosaic,
    web,
    )


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


class MultiItemConfigCtl(ConfigCtl, metaclass=ABCMeta):

    def __init__(self, cfg_item_creg=None):
        self._cfg_item_creg = cfg_item_creg

    def from_data(self, piece):
        config_template = self.empty_config_template()
        for item_ref in piece.items:
            item = self._cfg_item_creg.invite(item_ref)
            self.update_config(config_template, item)
        return config_template

    @abstractmethod
    def empty_config_template(self):
        pass

    @abstractmethod
    def update_config(self, config_template, item):
        pass

    def item_piece(self, item):
        return self._cfg_item_creg.actor_to_piece(item)

    def item_pieces_to_data(self, item_list):
        return htypes.system.item_list_config(
            items=tuple(
                mosaic.put(item)
                for item in item_list
                ),
            )


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


class DictConfigCtl(MultiItemConfigCtl):

    @classmethod
    def from_piece(cls, piece, cfg_item_creg):
        return cls(cfg_item_creg)

    @property
    def piece(self):
        return htypes.system.dict_config_ctl()

    def merge(self, dest, src):
        dest.update(src)

    def lazy_config(self, system, service_name, config_template):
        return LazyDictConfig(self, system, service_name, config_template)

    def resolve(self, system, service_name, config_template):
        config = {}
        for key, item in config_template.items():
            config[key] = self.resolve_item(system, service_name, item)
        return config

    def resolve_item(self, system, service_name, item):
        return item.resolve(system, service_name)

    def empty_config_template(self):
        return {}

    def update_config(self, config_template, item):
        config_template[item.key] = item


def service_pieces_to_config(service_to_config_piece):
    return htypes.system.system_config(tuple(
        htypes.system.service_config(
            service=service_name,
            config=mosaic.put(piece),
            )
        for service_name, piece in service_to_config_piece.items()
        ))


# Only MultiItemConfigCtl services are expected.
def merge_system_config_pieces(x, y):
    x_map = {
        rec.service: rec.config
        for rec in x.services
        }
    y_map = {
        rec.service: rec.config
        for rec in y.services
        }
    service_to_config_ref = {}
    for service_name in set([*x_map, *y_map]):
        x_config_ref = x_map.get(service_name)
        y_config_ref = y_map.get(service_name)
        if x_config_ref is not None and y_config_ref is not None:
            x_config = web.summon(x_config_ref)
            y_config = web.summon(y_config_ref)
            assert isinstance(x_config, htypes.system.item_list_config)
            assert isinstance(y_config, htypes.system.item_list_config)
            config = htypes.system.item_list_config(
                items=tuple(set([*x_config.items, *y_config.items])),
                )
            config_ref = mosaic.put(config)
        elif x_config_ref is not None:
            config_ref = x_config_ref
        else:
            config_ref = y_config_ref
        service_to_config_ref[service_name] = config_ref
    return htypes.system.system_config(tuple(
        htypes.system.service_config(
            service=service_name,
            config=config_ref,
            )
        for service_name, config_ref in service_to_config_ref.items()
        ))
