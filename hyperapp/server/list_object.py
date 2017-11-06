

MIN_ROWS_RETURNED = 100


def rows2fetched_chunk(key_column_id, all_rows, fetch_request, Chunk):
    assert fetch_request.desc_count == 0, repr(fetch_request.desc_count)  # Not yet supported
    sorted_rows = sorted(all_rows, key=fetch_request.sort_column_id)
    if fetch_request.from_key is None:
        idx = 0
    else:
        for idx, row in enumerate(sorted_rows):
            if getattr(row, key_column_id) > fetch_request.from_key:
                break
        else:
            idx = len(sorted_rows)
    asc_count = fetch_request.asc_count
    if asc_count < MIN_ROWS_RETURNED:
        asc_count = MIN_ROWS_RETURNED
    rows = sorted_rows[idx : idx+asc_count]
    bof = idx == 0
    eof = idx + asc_count >= len(sorted_rows)
    return Chunk(fetch_request.sort_column_id, fetch_request.from_key, rows, bof, eof)
