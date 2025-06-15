import inspect

from .services import (
    pyobj_creg,
    web,
    )
from .code.system_probe import Probe


class FixtureProbe(Probe):

    def __init__(self, system_probe, service_name, ctl_ref, fn, params):
        super().__init__(system_probe, service_name, fn, params)
        self._ctl_ref = ctl_ref

    def __repr__(self):
        return f"<FixtureProbe {self._fn} {self._params} {self._ctl_ref}>"



def resolve_fixture_cfg_item(piece):
    return (piece.service_name, piece)


def resolve_fixture_obj_cfg_value(piece, key, system, service_name):
    fn = pyobj_creg.invite(piece.function)
    probe = FixtureProbe(system, piece.service_name, piece.ctl, fn, piece.params)
    return probe.apply_obj()


def resolve_fixture_probe_cfg_value(piece, key, system, service_name):
    fn = pyobj_creg.invite(piece.function)
    probe = FixtureProbe(system, piece.service_name, piece.ctl, fn, piece.params)
    probe.apply_if_no_params()
    return probe
