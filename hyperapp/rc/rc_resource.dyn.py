class Resource:

    @property
    def import_records(self):
        return []

    @property
    def recorders(self):
        return {}

    def configure_system(self, system):
        pass

    def pick_constructors(self):
        return []
