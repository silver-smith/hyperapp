from . import htypes
from .code.mark import mark


@mark.global_command
def open_crud_sample():
    return htypes.sample_crud.model()


@mark.model
def list_crud_sample(piece):
    return [
        htypes.sample_crud.item(idx, f"item#{idx}", "Crud sample item #{idx}")
        for idx in range(10)
        ]
