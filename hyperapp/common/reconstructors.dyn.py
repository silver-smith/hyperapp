from .services import (
    reconstructors,
    )
from .code.type_reconstructor import type_to_piece


def register_reconstructors():
    reconstructors.extend([
        type_to_piece,
        ])
