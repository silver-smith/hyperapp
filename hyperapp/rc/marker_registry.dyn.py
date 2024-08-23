from functools import partial

from .services import pyobj_creg


class MarkerTemplate:

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

    def __repr__(self):
        return f"<MarkerTemplate {self._name}: {self._fn} {self._service_params}>"

    def resolve(self, system, service_name):
        if not self._service_params:
            return self._fn
        kw = {
            name: system.resolve_service(name)
            for name in self._service_params
            }
        return partial(self._fn, **kw)


class MarkerCfg:

    @classmethod
    def from_piece(cls, piece, service_name):
        template = MarkerTemplate.from_piece(piece)
        return cls(template)

    def __init__(self, template):
        self.key = template.name
        self.value = template

    @property
    def piece(self):
        return self.value.piece


def marker_registry(config, ctr_collector, marker_ctl):
    for name, marker in config.items():
        marker_ctl.set(name, marker)
    yield
    marker_ctl.clear()
