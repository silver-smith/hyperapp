from hyperapp.common.code_registry import CodeRegistry

from .services import (
  web,
  types,
  python_object_creg,
  )
from .service_decorator import service


def register_constructor(piece):
  t = python_object_creg.invite(piece.t)
  fn = python_object_creg.invite(piece.fn)
  constructor_creg.register_actor(t, fn)


service.constructor_creg = CodeRegistry('resource_ctr', web, types)
