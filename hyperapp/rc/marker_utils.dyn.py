import inspect
from collections import namedtuple

from .code.probe import real_fn


Params = namedtuple('Params', 'ctx_names service_names values')


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
        param_ofs = 1
    else:
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
    return Params(ctx_names, service_names, values)
