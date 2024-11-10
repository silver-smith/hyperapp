class ConfigItemMissingError(KeyError):

    def __init__(self, service_name, key, message=None):
        super().__init__(key)
        self.service_name = service_name
        self.key = key
