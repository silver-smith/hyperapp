from . import htypes
from .code.rc_requirement import Requirement


class MarkerReq(Requirement):

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.name)

    def __init__(self, name):
        self._name = name

    def __str__(self):
        return f"MarkerReq(name={self._name})"

    def __eq__(self, rhs):
        return type(rhs) == MarkerReq and rhs._name == self._name

    def __hash__(self):
        return hash(('service_req', self._name))

    @property
    def desc(self):
        return f"{self._name} marker"

    @property
    def piece(self):
        return htypes.marker_req.marker_req(self._name)

    def get_target(self, target_factory):
        raise NotImplementedError()

    def make_resource(self, target):
        raise NotImplementedError()
