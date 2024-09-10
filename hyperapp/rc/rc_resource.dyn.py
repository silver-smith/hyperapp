class Resource:

    # System resources should be applied first.
    @property
    def is_system_resource(self):
        return False

    @property
    def import_records(self):
        return []

    @property
    def recorders(self):
        return {}

    def configure_system(self, system):
        pass
