from .services import (
    pyobj_creg,
    )
from .tested.code import partial_ref as partial_ref_module


def _sample_fn(sample_param):
    return f'passed: {sample_param}'


def test_partial_ref(partial_ref):
    fn_ref = partial_ref(_sample_fn, sample_param='sample param')
    fn = pyobj_creg.invite(fn_ref)
    assert fn() == 'passed: sample param'
