import inspect
from collections import namedtuple

from .code.probe import real_fn


class Params:

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


def fn_params(fn):
    return list(inspect.signature(fn).parameters)


def split_params(fn, args, kw):
    fn_names = fn_params(fn)
    if args and is_cls_arg(fn, args[0]):
        # fn is a classmethod and args[0] is a 'cls' argument.
        called_class_name = args[0].__name__
        param_ofs = 1
    else:
        called_class_name = None
        param_ofs = 0
    args_values = {
        fn_names[idx]: arg
        for idx, arg in enumerate(args)
        }
    values = {
        **args_values,
        **kw,
        }
    ctx_names = [
        *fn_names[param_ofs:len(args)],
        *kw,
        ]
    service_names = [
        name for name in fn_names[param_ofs:]
        if name not in ctx_names
        ]
    return Params(called_class_name, ctx_names, service_names, values)
