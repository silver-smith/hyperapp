from .services import (
    generate_rsa_identity,
    mark,
    )


@mark.service
def mock_identity():
    return generate_rsa_identity(fast=True)
