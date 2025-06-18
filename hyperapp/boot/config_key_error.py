class ConfigItemMissingError(Exception):

    def __init__(self, service_name, key):
        self.service_name = service_name
        self.key = key


class ConfigKeyError(KeyError, ConfigItemMissingError):

    def __init__(self, service_name, key):
        KeyError.__init__(self, key)
        ConfigItemMissingError.__init__(self, service_name, key)

    def __str__(self):
        return f"Missing service {self.service_name!r} key: {self.key!r}"
