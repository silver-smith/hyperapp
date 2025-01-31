import re

from .services import (
    web,
    )


_shortcut_re = re.compile(r'([A-Z][A-Za-z]*\+)*[A-Z][A-Za-z0-9]*$')


def string_name(piece, gen):
    if _shortcut_re.match(piece):
        return 'shortcut_' + piece.replace('+', '_')
    return None


def record_mt_name(piece, gen):
    return f'{piece.name}_record_mt'


def call_name(piece, gen):
    fn, t = web.summon_with_t(piece.function)
    base_stem = gen.make_stem(fn, t)
    return f'{base_stem}_call'
