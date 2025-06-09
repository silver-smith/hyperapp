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

    def __contains__(self, key):
        return key in self._config

    def __setitem__(self, key, value):
        self._config[key] = value

    def __delitem__(self, key):
        del self._config[key]

    def get(self, key):
        return self._config.get(key)


def assoc_key(config, assoc_key_creg, system):
    return AssociationKeyRegistry(system, assoc_key_creg, config)


class KeyBaseAssociation:

    @classmethod
    def from_piece(cls, piece):
        return cls()

    def __init__(self):
        pass
