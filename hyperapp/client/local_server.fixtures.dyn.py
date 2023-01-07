from .services import (
    mark,
    )


class _PhonyFileBundle:

    def load_piece(self):
        return None


@mark.service
def local_server_ref():
    return _PhonyFileBundle()
