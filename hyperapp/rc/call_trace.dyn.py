import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass
class CallTrace:

    module_name: str
    line_no: int
    fn_qual_name: str
    obj_type: str
    params: dict

    @classmethod
    def from_piece(cls, piece):
        params = {
            p.name: web.summon(p.t)
            for p in piece.params
            }
        log.info("Call trace: %s:%d: %s %s (%s)", piece.module, piece.line_no, piece.fn_qual_name, piece.obj_type or '-', params)
        return cls(piece.module, piece.line_no, piece.fn_qual_name, piece.obj_type, params)
