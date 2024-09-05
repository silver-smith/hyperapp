import inspect


def check_is_function(fn):
    if not inspect.isfunction(fn):
        raise RuntimeError(
            f"Unknown object attempted to be marked as an actor: {fn!r};"
            " Expected function, classmethod or staticmethod"
            )


def check_not_classmethod(fn):
    if type(fn) is classmethod:
        raise RuntimeError(
            f"Wrap this method first with marker and then with classmethod (classmethod should be first): {fn!r}"
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
