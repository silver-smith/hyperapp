# http://stackoverflow.com/questions/24601722/how-can-i-use-functools-singledispatch-with-instance-methods

from functools import singledispatch, update_wrapper


def method_dispatch(func):
    dispatcher = singledispatch(func)
    def wrapper(*args, **kw):
        return dispatcher.dispatch(args[1].__class__)(*args, **kw)
    wrapper.register = dispatcher.register
    update_wrapper(wrapper, func)
    return wrapper
