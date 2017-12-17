from operator import attrgetter


MIN_ROWS_RETURNED = 100


def rows2fetched_chunk(key_column_id, all_rows, fetch_request, Chunk):
    sorted_rows = sorted(all_rows, key=attrgetter(fetch_request.sort_column_id))
    if fetch_request.from_key is None:
        idx = 0
    else:
        for idx, row in enumerate(sorted_rows):
            if getattr(row, key_column_id) > fetch_request.from_key:
                break
        else:
            idx = len(sorted_rows)
    start = max(0, idx - fetch_request.desc_count)
    end = idx + fetch_request.asc_count
    if end - start < MIN_ROWS_RETURNED:
        end = start + MIN_ROWS_RETURNED
        if end < idx + 1:
            end = idx + 1
    if end > len(sorted_rows):
        end = len(sorted_rows)
    rows = sorted_rows[start:end]
    bof = start == 0
    eof = end == len(sorted_rows)
    return Chunk(fetch_request.sort_column_id, fetch_request.from_key, rows, bof, eof)
