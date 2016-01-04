from ..common.interface import tStringFieldHandle, tIntFieldHandle


def stringFieldHandle( value=None ):
    return tStringFieldHandle.instantiate('string', value or '')

def intFieldHandle( value ):
    return tIntFieldHandle.instantiate('int', value)

