from functools import partial

from . import htypes


# Only items converted from data can be converted to data.
class OneWayKeyCtl:

    @classmethod
    def from_piece(cls, piece, cfg_item_creg):
        return cls(cfg_item_creg)

    def __init__(self, cfg_item_creg):
        self._cfg_item_creg = cfg_item_creg

    @property
    def piece(self):
        return htypes.system.one_way_key_ctl()

    def data_to_item(self, piece):
        key, template = self._cfg_item_creg.animate(piece)
        return (key, template)

    def item_to_data(self, key, template):
        return self._cfg_item_creg.actor_to_piece((key, template))



def config_key_ctl_creg_config(cfg_item_creg):
    return {
        htypes.system.one_way_key_ctl: partial(OneWayKeyCtl.from_piece, cfg_item_creg=cfg_item_creg),
        }
