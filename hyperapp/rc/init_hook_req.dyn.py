from dataclasses import dataclass

from . import htypes
from .code.rc_requirement import Requirement


@dataclass(frozen=True)
class InitHookReq(Requirement):
    var_name: str

    @classmethod
    def from_piece(cls, piece):
        return cls(
            var_name=piece.var_name,
            )

    @property
    def piece(self):
        return htypes.init_hook_req.init_hook_req(
            var_name=self.var_name,
            )
