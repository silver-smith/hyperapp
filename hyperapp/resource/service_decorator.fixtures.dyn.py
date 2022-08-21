from .marker import param


def _dummy_fn():
  pass


param.service.fn = _dummy_fn
