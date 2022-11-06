from .marker import service


class _PhonyFileBundle:

    def load_piece(self):
        return None


service.local_server_ref = _PhonyFileBundle()
