from .module import get_this_module, ThisModule
from .navigator import View


def get_item_type():
    return get_this_module().item_type

def get_state_type():
    return get_this_module().state_type
