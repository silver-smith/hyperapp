class ConfigKeyError(KeyError):

    def __init__(self, service_name, key):
        super().__init__(key)
        self.service_name = service_name
        self.key = key

    def __str__(self):
        return f"ConfigKeyError for {self.service_name}: {self.key!r}"
