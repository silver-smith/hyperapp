from .services import pyobj_creg
from .code.system import NotATemplate


class Marker:

    @classmethod
    def from_piece(cls, piece):
        return cls(
            name=piece.name,
            fn=pyobj_creg.invite(piece.function),
            service_params=piece.service_params,
            )

    def __init__(self, name, fn, service_params):
        self.name = name
        self._fn = fn
        self._service_params = service_params


class MarkerCfg:

    @classmethod
    def from_piece(cls, piece, service_name):
        marker = Marker.from_piece(piece)
        return cls(marker)

    def __init__(self, marker):
        self.key = marker.name
        self._marker = marker
        self.value = NotATemplate(marker)

    @property
    def piece(self):
        return self._marker.piece


def marker_registry(config, ctr_collector):
    assert 0, config
    for name, marker in config.items():
        pass
