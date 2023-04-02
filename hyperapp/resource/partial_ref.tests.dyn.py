from .services import (
    python_object_creg,
    )
from .tested.services import partial_ref


def _sample_fn(sample_param):
    return f'passed: {sample_param}'


def test_partial_ref():
    fn_ref = partial_ref(_sample_fn, sample_param='sample param')
    fn = python_object_creg.invite(fn_ref)
    assert fn() == 'passed: sample param'
