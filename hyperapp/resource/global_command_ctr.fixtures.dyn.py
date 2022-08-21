from .marker import param


def _dummy_fn():
  pass


param.global_command.fn = _dummy_fn
