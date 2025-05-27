import inspect
from collections import namedtuple

from .code.probe import real_fn



class ServiceParams:

    def __init__(self, called_class_name, free_names, service_names, values, has_config=False):
        self._called_class_name = called_class_name
        self.free_names = free_names
        self.service_names = service_names
        self.values = values
        self.has_config = has_config


class ActorParams:

    def __init__(self, called_class_name, ctx_names, service_names, values):
        self._called_class_name = called_class_name
        self.ctx_names = ctx_names
        self.service_names = service_names
        self.values = values

    # Class method may be implemented in base class.
    # But we need actual (called) class name in qual_name list.
    def real_qual_name(self, fn):
        qual_name_l = fn.__qualname__.split('.')
        if self._called_class_name:
            assert len(qual_name_l) > 1
            return [self._called_class_name, *qual_name_l[1:]]
        return qual_name_l


def check_is_function(fn):
    rfn = real_fn(fn)
    if not inspect.isfunction(rfn):
        raise RuntimeError(
            f"Unknown object attempted to be marked as an actor: {rfn!r};"
            " Expected function, classmethod or staticmethod"
            )


def check_not_classmethod(fn):
    rfn = real_fn(fn)
    if type(rfn) is classmethod:
        raise RuntimeError(
            f"Wrap this method first with marker and then with classmethod (classmethod should be first): {rfn!r}"
            )

    
def is_cls_arg(fn, arg):
    # Check arg is a class (MyClass).
    if not isinstance(arg, type):
        return False
    # Resolve MyClass.my_function attribute.
    attr = getattr(arg, fn.__name__, None)
    if attr is None:
        return False
    # Check if class MyClass.my_function is bound to is arg.
    return getattr(attr, '__self__', None) is arg


def split_service_params(fn, args, kw):
    fn_params = inspect.signature(fn).parameters
    param_names = list(fn_params)
    if args and is_cls_arg(fn, args[0]):
        # fn is a classmethod and args[0] is a 'cls' argument.
        called_class_name = args[0].__name__
        ofs = 1
    else:
        called_class_name = None
        ofs = 0
    has_config = 'config' in fn_params
    if has_config:
        if param_names[ofs] != 'config':
            raise RuntimeError(f"{fn}: 'config' should be first parameter: {', '.join(param_names)}")
        ofs += 1
    free_param_count = len(args) + len(kw)
    service_param_count = len(fn_params) - free_param_count - ofs
    service_names = param_names[ofs:ofs + service_param_count]
    args_values = {
        param_names[idx]: arg
        for idx, arg in enumerate(args[ofs + service_param_count:])
        }
    values = {
        **args_values,
        **kw,
        }
    free_names = param_names[ofs + service_param_count:]
    return ServiceParams(called_class_name, free_names, service_names, values, has_config)


def split_actor_params(fn, args, kw):
    fn_params = inspect.signature(fn).parameters
    param_names = list(fn_params)
    if args and is_cls_arg(fn, args[0]):
        # fn is a classmethod and args[0] is a 'cls' argument.
        called_class_name = args[0].__name__
        ofs = 1
    else:
        called_class_name = None
        ofs = 0
    args_values = {
        param_names[idx]: arg
        for idx, arg in enumerate(args)
        }
    values = {
        **args_values,
        **kw,
        }
    ctx_names = [
        *param_names[ofs:len(args)],
        *kw,
        ]
    service_names = [
        name for name in param_names[ofs:]
        if name not in ctx_names
        ]
    return ActorParams(called_class_name, ctx_names, service_names, values)


def process_awaitable_result(fn, result, *args, **kw):
    if not inspect.iscoroutine(result):
        fn(result, *args, **kw)
        return result
    async def await_result():
        real_result = await result
        fn(real_result, *args, **kw)
        return real_result
    return await_result()
