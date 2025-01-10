from .htypes import ref_t
from .ref import ref_repr


type_repr_registry = {
    ref_t: ref_repr,
    }
