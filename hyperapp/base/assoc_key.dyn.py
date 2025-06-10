from .services import (
    code_registry_ctr,
    )


def assoc_key_creg(config):
    return code_registry_ctr('assoc_key_creg', config)


class AssociationKeyRegistry:

    def __init__(self, system, assoc_key_creg, config):
        self._system = system
        self._assoc_key_creg = assoc_key_creg
        self._config = config

    def init(self, system):
        system.add_config_hook(self)

    def __contains__(self, key):
        return key in self._config

    def __setitem__(self, key, value):
        self._config[key] = value

    def __delitem__(self, key):
        del self._config[key]

    def get(self, key):
        return self._config.get(key)

    # System config hook method
    def config_item_set(self, service_name, cfg_item):
        assert 0, (service_name, cfg_item)

    # System config hook method
    def config_item_removed(self, service_name, cfg_item):
        assert 0, (service_name, cfg_item)


def assoc_key(config, assoc_key_creg, system):
    return AssociationKeyRegistry(system, assoc_key_creg, config)


def init_assoc_key(assoc_key, system):
    assoc_key.init(system)


class KeyBaseAssociation:

    @classmethod
    def from_piece(cls, piece):
        return cls()

    def __init__(self):
        pass
