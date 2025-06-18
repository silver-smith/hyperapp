from hyperapp.boot.htypes import Type
from hyperapp.boot.config_key_error import ConfigItemMissingError

from .code.mark import mark


@mark.service
def format(formatter_creg, piece):
    if isinstance(piece, Type):
        return str(piece)
    try:
        return formatter_creg.animate(piece)
    except ConfigItemMissingError as x:
        if x.service_name != 'formatter_creg':
            raise
    return str(piece)
