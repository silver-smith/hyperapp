class Resource:

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

    def configure_system(self, system):
        pass
