from . import htypes
from .services import (
    mosaic,
    )


def browse_current_model(piece):
    return htypes.data_browser.data_browser(
        data=mosaic.put(piece),
        )
