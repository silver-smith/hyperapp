# Store servant wrapper to separate module to avoid unneeded dependencies.

import logging

from .code.context import Context

log = logging.getLogger(__name__)


def list_wrapper(servant_fn_piece, system_fn_creg, **kw):
    servant_fn = system_fn_creg.animate(servant_fn_piece)
    log.info("List servant wrapper: Loading items using %s", servant_fn)
    ctx = Context(**kw)
    item_list = servant_fn.call(ctx)
    return item_list
