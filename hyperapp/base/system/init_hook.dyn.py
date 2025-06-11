from .code.context import Context


class InitHooks:

  def __init__(self, config):
      self._config = config

  def run_hooks(self):
      ctx = Context()
      for hook in self._config:
          hook.call(ctx)


def init_hook(config):
    return InitHooks(config)
