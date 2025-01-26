from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.mark import mark
from .code.config_ctl import ConfigCtl, item_pieces_to_data


class DataServiceConfigCtl(ConfigCtl):

    @classmethod
    @mark.actor.config_ctl_creg
    def from_piece(cls, piece):
        return cls()

    def from_data(self, piece):
        config_template = self.empty_config_template()
        for item_ref in piece.items:
            item = web.summon(item_ref)
            key = web.summon(item.key)
            value = web.summon(item.value)
            self._update_config(config_template, key, value)
        return config_template

    def to_data(self, config):
        return item_pieces_to_data([
            self._item_piece(key, value)
            for key, value in config.items()
            ])

    def empty_config_template(self):
        return {}

    def merge(self, dest, src):
        dest.update(src)

    def resolve(self, system, service_name, config_template):
        return DataServiceConfig(system, system.default_layer, service_name)

    @staticmethod
    def _update_config(config_template, key, value):
        config_template[key] = value

    @staticmethod
    def _item_piece(key, value):
        return htypes.data_service.config_item(
            key=mosaic.put(key),
            value=mosaic.put(value),
            )


class DataServiceConfig:

    def __init__(self, system, target_layer, service_name):
        self._system = system
        self._target_layer = target_layer
        self._service_name = service_name

    def __getitem__(self, key):
        config = self._system.get_config_template(self._service_name)
        return config[key]

    def __setitem__(self, key, value):
        self._target_layer.set(self._service_name, key, value)
