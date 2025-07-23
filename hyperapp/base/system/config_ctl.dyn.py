from abc import ABCMeta, abstractmethod
from functools import partial

from hyperapp.boot.config_key_error import ConfigKeyError

from . import htypes
from .services import (
    mosaic,
    web,
    )


class ActorValueCtl:

    @classmethod
    def from_piece(cls, piece, cfg_value_creg):
        return cls(cfg_value_creg)

    def __init__(self, cfg_value_creg=None):
        self._cfg_value_creg = cfg_value_creg

    # def init(self, cfg_value_creg):
    #     self._cfg_value_creg = cfg_value_creg

    @property
    def piece(self):
        return htypes.system.actor_value_ctl()

    def resolve(self, template, key, system, service_name):
        return self._cfg_value_creg.animate(template, key, system, service_name)

    def reverse(self, value):
        return value.piece


class DataValueCtl:

    @classmethod
    def from_piece(cls, piece):
        return cls()

    # def init(self, cfg_value_creg):
    #     pass

    @property
    def piece(self):
        return htypes.system.data_value_ctl()

    def resolve(self, template, key, system, service_name):
        return template

    def reverse(self, value):
        return value


def config_value_ctl_creg_config(cfg_value_creg):
    return {
        htypes.system.actor_value_ctl: partial(ActorValueCtl.from_piece, cfg_value_creg=cfg_value_creg),
        htypes.system.data_value_ctl: DataValueCtl.from_piece,
        }


class ConfigCtl(metaclass=ABCMeta):

    is_multi_item = False

    @abstractmethod
    def from_data(self, piece):
        pass

    @abstractmethod
    def to_data(self, config):
        pass

    @abstractmethod
    def empty_config_template(self):
        pass

    @abstractmethod
    def merge(self, dest, src):
        pass

    @abstractmethod
    def resolve(self, system, service_name, config_template):
        pass


class MultiItemConfigCtl(ConfigCtl, metaclass=ABCMeta):

    is_multi_item = True

    def __init__(self, cfg_item_creg=None, cfg_value_creg=None):
        self._cfg_item_creg = cfg_item_creg
        self._cfg_value_creg = cfg_value_creg

    def from_data(self, piece):
        config_template = self.empty_config_template()
        for item_ref in piece.items:
            item = web.summon(item_ref)
            key, template = self.data_to_item(item)
            self._update_config(config_template, key, template)
        return config_template

    def to_data(self, config_template):
        item_pieces = self._config_to_item_pieces(config_template)
        return self._item_pieces_to_data(item_pieces)

    def _config_to_item_pieces(self, config_template):
        return [
            self.item_to_data(key, template)
            for key, template in self.config_to_items(config_template)
            ]

    @staticmethod
    def config_to_items(config_template):
        return config_template.items()

    @abstractmethod
    def _update_config(self, config_template, key, template):
        pass

    def data_to_item(self, item):
        key, template = self._cfg_item_creg.animate(item)
        return (key, template)

    def item_to_data(self, key, template):
        return self._cfg_item_creg.actor_to_piece((key, template))

    def _item_pieces_to_data(self, item_list):
        return item_pieces_to_data(item_list)


class LazyDictConfig:

    def __init__(self, ctl, system, service_name, config_template):
        self._ctl = ctl
        self._system = system
        self._service_name = service_name
        self._config_template = config_template  # key -> template
        self._resolved_config = {}

    def __getitem__(self, key):
        return self._resolve_key(key)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def items(self):
        return self._items.items()

    def values(self):
        return self._items.values()

    @property
    def _items(self):
        items = {**self._resolved_config}
        for key, value_template in self._config_template.items():
            if key in items:
                continue
            value = self._resolve_template(key, value_template)
            items[key] = value
        return items

    def setdefault(self, key, default):
        try:
            return self._resolve_key(key)
        except KeyError:
            self._resolved_config[key] = default
            return default

    def update(self, config):
        self._resolved_config.update(config)

    def _resolve_key(self, key):
        try:
            return self._resolved_config[key]
        except KeyError:
            pass
        value_template = self._config_template[key]  # KeyError is raised from here.
        return self._resolve_template(key, value_template)

    def _resolve_template(self, key, value_template):
        try:
            value = self._ctl.resolve_value(self._system, self._service_name, key, value_template)
        except ConfigKeyError as x:
            if x.service_name == 'cfg_value_creg':
                raise
            # This is not a key error for the caller.
            raise RuntimeError(
                f"Error resolving {self._service_name} config tempate for {key!r}: {x.__class__.__name__}: {x}") from x
        self._resolved_config[key] = value
        return value


class DictConfigCtl(MultiItemConfigCtl):

    @classmethod
    def from_piece(cls, piece, config_value_ctl_creg, cfg_item_creg, cfg_value_creg):
        value_ctl = config_value_ctl_creg.invite(piece.value_ctl)
        return cls(value_ctl, cfg_item_creg, cfg_value_creg)

    def __init__(self, value_ctl=None, cfg_item_creg=None, cfg_value_creg=None):
        super().__init__(cfg_item_creg, cfg_value_creg)
        self._value_ctl = value_ctl or ActorValueCtl(cfg_value_creg)

    @property
    def piece(self):
        return htypes.system.dict_config_ctl(
            value_ctl=mosaic.put(self._value_ctl.piece),
            )

    def merge(self, dest, src):
        dest.update(src)
        return dest

    def _lazy_config(self, system, service_name, config_template):
        return LazyDictConfig(self, system, service_name, config_template)

    def resolve(self, system, service_name, config_template):
        return self._lazy_config(system, service_name, config_template)

    def resolve_value(self, system, service_name, key, template):
        return self._value_ctl.resolve(template, key, system, service_name)

    def empty_config_template(self):
        return {}

    def _update_config(self, config_template, key, template):
        config_template[key] = template


class FlatListConfigCtl(MultiItemConfigCtl):

    @classmethod
    def from_piece(cls, piece, cfg_item_creg, cfg_value_creg):
        return cls(cfg_item_creg, cfg_value_creg)

    @property
    def piece(self):
        return htypes.system.flat_list_config_ctl()

    @staticmethod
    def config_to_items(config_template):
        return [(None, template) for template in config_template]

    def empty_config_template(self):
        return []

    def _update_config(self, config_template, key, template):
        assert key is None
        config_template.append(template)

    def merge(self, dest, src):
        dest.extend(src)
        return dest

    def resolve(self, system, service_name, config_template):
        config = []  # command list.
        key = None
        for template in config_template:
            value = self._cfg_value_creg.animate(template, key, system, service_name)
            config.append(value)
        return config


def service_pieces_to_config(service_to_config_piece):
    return htypes.system.system_config(tuple(
        htypes.system.service_config(
            service=service_name,
            config=mosaic.put(piece),
            )
        for service_name, piece in service_to_config_piece.items()
        ))


def item_pieces_to_data(item_list):
    return htypes.system.item_list_config(
        items=tuple(
            mosaic.put(item)
            for item in item_list
            ),
        )


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
                # Preserve sorting order. Duplicates are ok.
                items=tuple([*x_config.items, *y_config.items]),
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
