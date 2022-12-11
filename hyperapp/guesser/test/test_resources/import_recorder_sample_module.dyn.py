from . import htypes
from .htypes import sample_types
from .htypes.sample_types import sample_rec

from .htypes.sample_types import another_rec


print("sample type 1: %s", htypes.sample_types.sample_rec)
print("sample type 2: %s", sample_types.sample_rec)
print("sample type 3: %s", sample_rec)

print("another type 3: %s", another_rec)

assert htypes.sample_types.sample_rec is sample_types.sample_rec
assert htypes.sample_types.sample_rec is sample_rec


def sample_fn():
    pass
