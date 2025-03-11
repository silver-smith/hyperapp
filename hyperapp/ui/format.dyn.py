from hyperapp.boot.config_item_missing import ConfigItemMissingError

from .code.mark import mark


@mark.service
def format(formatter_creg, piece):
    try:
        return formatter_creg.animate(piece)
    except ConfigItemMissingError as x:
        if x.service_name != 'formatter_creg':
            raise
    return str(piece)
