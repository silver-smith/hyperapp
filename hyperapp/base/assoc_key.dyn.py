from .services import (
    association_reg,
    code_registry_ctr,
    )


def assoc_key_creg(config):
    return code_registry_ctr('assoc_key_creg', config)


class AssociationKeyRegistry:

    def __init__(self, system, config_ctl, assoc_key_creg, config):
        self._system = system
        self._config_ctl = config_ctl
        self._assoc_key_creg = assoc_key_creg
        self._config = config

    def init(self, system):
        system.add_config_hook(self)
        association_reg.set_hook(self.on_assocation_received)

    def __contains__(self, key):
        return key in self._config

    def __setitem__(self, key, value):
        self._config[key] = value

    def __delitem__(self, key):
        del self._config[key]

    def get(self, key):
        return self._config.get(key)

    # System config hook method
    def config_item_set(self, service_name, key, template):
        try:
            assoc_key_piece = self._config[service_name]
        except KeyError:
            return
        assoc_key = self._assoc_key_creg.animate(assoc_key_piece)
        bases = assoc_key.bases(key, template)
        ctl = self._config_ctl[service_name]
        item_piece = ctl.item_piece(key, template)
        association_reg.set_association(bases, service_name, item_piece)

    # System config hook method
    def config_item_removed(self, service_name, key, template):
        ctl = self._config_ctl[service_name]
        item_piece = ctl.item_piece(key, template)
        association_reg.remove_association(service_name, item_piece)

    def on_assocation_received(self, service_name, cfg_item):
        try:
            assoc_key_piece = self._config[service_name]
        except KeyError:
            return
        assoc_key = self._assoc_key_creg.animate(assoc_key_piece)
        ctl = self._config_ctl[service_name]
        key, template = ctl.resolve_cfg_item(cfg_item)
        self._system.default_layer.set(service_name, key, template)


def assoc_key(config, assoc_key_creg, config_ctl, system):
    return AssociationKeyRegistry(system, config_ctl, assoc_key_creg, config)


def init_assoc_key(assoc_key, system):
    assoc_key.init(system)


class KeyBaseAssociation:

    @classmethod
    def from_piece(cls, piece):
        return cls()

    @staticmethod
    def bases(key, template):
        return [key]
