# Store servant wrapper to separate module to avoid unneeded dependencies.

from .services import (
    pyobj_creg,
    )


def index_tree_wrapper(servant_ref):
    servant = pyobj_creg.invite(servant_ref)
    return servant()


def key_tree_wrapper(servant_ref, key_field):
    servant = pyobj_creg.invite(servant_ref)
    return servant()
