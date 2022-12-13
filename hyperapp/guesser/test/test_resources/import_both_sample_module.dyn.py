from . import htypes
from .code import (
    code_module_1,
    code_module_2,
    )
from .services import (
    service_1,
    service_2,
    )
from .tested.code.code_module_3 import tested_attr


print("sample type 1: %s", htypes.sample_types.sample_rec)

code_module_1_attr = code_module_1.attr
service_1_attr_nested = service_1.attr.nested


def sample_fn():
    pass
