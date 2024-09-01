from .tested.code import client


def test_client(client_main):
    sys_argv = [
        '--clean=true',
        '--lcs-storage-path=/tmp/client-test-lcs-storage-path.yaml',
        '--layout-path=/tmp/client-test-layout-path.jaon',
        ]
    client_main(sys_argv)
