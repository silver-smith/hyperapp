
class ServiceCtr:

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.attr_name, piece.name)

    def __init__(self, attr_name, name):
        self._attr_name = attr_name
        self._name = name

    def update_targets(self, resource_target, target_factory):
        service_found_tgt = target_factory.service_found(self._name)
        service_found_tgt.set_provider(resource_target, self._attr_name)
