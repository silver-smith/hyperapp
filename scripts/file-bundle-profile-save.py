import cProfile
import pstats
from pathlib import Path

path = Path.home() / '.local/share/hyperapp/rc-job-cache.cdr'
b = file_bundle_factory(path, 'cdr')
print('bundle:', b)
p = b.load_piece()

out_b = file_bundle_factory(Path('/tmp/test.cdr'), 'cdr2')
def test_save():
    out_b.save_piece(p)

print("First save")
test_save()  # Populate ref picker cache.

print("Second save - profiling")
with cProfile.Profile() as pr:
    pr.runcall(test_save)
    stats = pstats.Stats(pr)

stats.dump_stats('/tmp/file-bundle.profile')

stats.sort_stats('cumulative')
stats.print_stats()

stats.sort_stats('time')
stats.print_stats()
