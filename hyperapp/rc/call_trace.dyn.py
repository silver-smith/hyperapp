import logging
from dataclasses import dataclass
from typing import Any

log = logging.getLogger(__name__)

from .services import (
    web,
    )


@dataclass
class CallTrace:

    module_name: str
    line_no: int
    fn_qual_name: str
    obj_type: str
    params: dict
    result_t: Any

    @classmethod
    def from_piece(cls, piece):
        params = {
            p.name: web.summon(p.t)
            for p in piece.params
            }
        result_t = web.summon(piece.result_t)
        log.info("Call trace: %s:%d: %s %s (%s) -> %s",
                 piece.module, piece.line_no, piece.fn_qual_name, piece.obj_type or '-', params, result_t)
        return cls(piece.module, piece.line_no, piece.fn_qual_name, piece.obj_type, params, result_t)
