from hyperapp.common.code_registry import CodeRegistry

from .services import (
  web,
  types,
  )
from .service_decorator import service


service.constructor_creg = CodeRegistry('resource_ctr', web, types)
