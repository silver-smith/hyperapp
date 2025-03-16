import time
from timeit import timeit, repeat
from pathlib import Path

path = Path.home() / '.local/share/hyperapp/rc-job-cache.cdr'
b = file_bundle_factory(path, 'cdr')
print('bundle:', b)

# timer = time.process_time
timer = time.perf_counter  # default

print("Load:")
for t in repeat(b.load_piece, number=1, repeat=5, timer=timer):
    print(t)

p = b.load_piece()

print("Save:")
out_b = file_bundle_factory(Path('/tmp/test.cdr'), 'cdr')
def test_save():
    out_b.save_piece(p)

for t in repeat(test_save, number=1, repeat=5, timer=timer):
    print(t)
