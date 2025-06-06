class Resource:

    def __eq__(self, rhs):
        raise NotImplementedError()

    # System resources should be applied first.
    @property
    def is_system_resource(self):
        return False

    # Service resources should be applied second.
    # Regular resources should be applied last.
    @property
    def is_service_resource(self):
        return False

    @property
    def import_records(self):
        return []

    @property
    def recorders(self):
        return {}

    # Service -> item list.
    @property
    def system_config_items(self):
        return {}

    # Service -> item list.
    @property
    def system_config_items_override(self):
        return {}

    def configure_system(self, system):
        pass

    @property
    def tested_modules(self):
        return []
