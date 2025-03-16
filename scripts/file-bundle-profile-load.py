# ~/shell.sh scripts/file-bundle-profile-load.py

import cProfile
import pstats
from pathlib import Path

path = Path.home() / '.local/share/hyperapp/rc-job-cache.cdr'
b = file_bundle_factory(path, 'cdr')
print('bundle:', b)

print("Load - profiling")
with cProfile.Profile() as pr:
    pr.runcall(b.load_piece)
    stats = pstats.Stats(pr)

stats.dump_stats('/tmp/file-bundle-first-load.profile')

stats.sort_stats('cumulative')
stats.print_stats()

stats.sort_stats('time')
stats.print_stats()
