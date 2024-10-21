class ConfigItemMissingError(Exception):

    def __init__(self, service_name, key):
        super().__init__(f"Configuration item is missing for {service_name}: {key}")
        self.service_name = service_name
        self.key = key
