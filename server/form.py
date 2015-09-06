from common.interface import tStringFieldHandle, tIntFieldHandle


def stringFieldHandle( value=None ):
    return tStringFieldHandle.instantiate('string_field', value or '')

def intFieldHandle( value ):
    return tIntFieldHandle.instantiate('int_field', value)

