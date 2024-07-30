class Resource:

    @property
    def import_records(self):
        return []

    @property
    def recorders(self):
        return {}

    @property
    def config_triplets(self):
        return []

    @property
    def config_item_fixtures(self):
        return []

    def update_targets(self, target_factory):
        pass
