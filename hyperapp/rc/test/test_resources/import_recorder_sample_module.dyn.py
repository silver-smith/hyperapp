from . import htypes
from .htypes import sample_types
from .htypes.sample_types import sample_rec

from .htypes.sample_types import another_rec


print(f"sample type 1: {htypes.sample_types.sample_rec}")
print(f"sample type 2: {sample_types.sample_rec}")
print(f"sample type 3: {sample_rec}")

print(f"another type 3: {another_rec}")

assert htypes.sample_types.sample_rec is sample_types.sample_rec
assert htypes.sample_types.sample_rec is sample_rec


def sample_fn():
    pass
