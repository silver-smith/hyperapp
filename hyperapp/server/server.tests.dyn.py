from pathlib import Path
from unittest.mock import Mock

from .code.mark import mark
from .tested.code import server


@mark.fixture
def stop_signal():
    return Mock()


def test_server(server_main):
    project = None
    identity_path = Path('/tmp/server-test-identity.json')
    try:
        identity_path.unlink()
    except FileNotFoundError:
        pass
    sys_argv = [
        f'--identity-path={identity_path}',
        ]
    server_main(project, sys_argv)
