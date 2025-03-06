

def test_bool_does_not_replace_int(mosaic, web):
    _ = mosaic.put(True)  # Cached now.
    ref = mosaic.put(1)  # Should not pick previously cached bool.
    value = web.summon(ref)
    assert type(value) is int
