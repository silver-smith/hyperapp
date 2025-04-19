# Store servant wrapper to separate module to avoid unneeded dependencies.

import logging

from .services import (
    pyobj_creg,
    )
from .code.context import Context

log = logging.getLogger(__name__)


def list_wrapper(servant_fn_piece, model, key_field_t, system_fn_creg, model_servant, **kw):
    servant_fn = system_fn_creg.animate(servant_fn_piece)
    servant = model_servant(model)
    servant.set_servant_fn(
        key_field_t=pyobj_creg.animate_opt(key_field_t),
        fn=servant_fn,
        )
    log.info("List servant wrapper: Loading items using %s", servant_fn)
    ctx = Context(**kw)
    item_list = servant_fn.call(ctx)
    return item_list
