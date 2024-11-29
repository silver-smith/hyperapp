import logging

from . import htypes
from .code.mark import mark
from .code.sample_list import sample_list

log = logging.getLogger(__name__)


@mark.crud.get
def sample_list_get(piece, id):
    item_to_id = {
        item.id: item
        for item in sample_list(piece)
        }
    item = item_to_id[id]
    return htypes.sample_list_crud.form_item(
        title=item.title,
        desc=item.desc,
        )


@mark.crud.update
def sample_list_update(piece, id, value):
    log.info("Sample CRUD: Update %s #%d: %s", piece, id, value)
