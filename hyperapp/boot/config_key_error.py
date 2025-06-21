
class ConfigKeyError(KeyError):

    def __init__(self, service_name, key):
        super().__init__(key)
        self.service_name = service_name
        self.key = key

    def __str__(self):
        return f"Missing service {self.service_name!r} key: {self.key!r}"
