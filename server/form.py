from common.interface import tStringFieldHandle, tIntFieldHandle


def stringFieldHandle( value ):
    return tStringFieldHandle.instantiate('string_field', value)

def intFieldHandle( value ):
    return tIntFieldHandle.instantiate('int_field', value)

