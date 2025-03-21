from pathlib import Path
from unittest.mock import Mock

from .code.mark import mark
from .tested.code import server


@mark.fixture
def stop_signal():
    return Mock()


def test_server(server_main):
    name_to_project = None
    identity_path = Path('/tmp/server-test-identity.json')
    try:
        identity_path.unlink()
    except FileNotFoundError:
        pass
    sys_argv = [
        f'--identity-path={identity_path}',
        '--port=0',  # Use ephemeral instead of default.
        ]
    server_main(name_to_project, sys_argv)
