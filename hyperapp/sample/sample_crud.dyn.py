import logging

from . import htypes
from .code.mark import mark

log = logging.getLogger(__name__)


@mark.global_command
def open_crud_sample():
    return htypes.sample_crud.model()


@mark.model
def list_crud_sample(piece):
    return [
        htypes.sample_crud.item(idx, f"item#{idx}", "Crud sample item #{idx}")
        for idx in range(10)
        ]


@mark.crud.get
def get_crud_sample(piece, current_item):
    return htypes.sample_crud.edit_item(
        id=current_item.id,
        name=current_item.name,
        desc=current_item.desc,
        )


@mark.crud.update
def update_crud_sample(piece, value):
    log.info("Sample CRUD: Update %s: %s", piece, value)
