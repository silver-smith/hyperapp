import sys
import os
import os.path

sys.path.insert(0, os.path.expanduser('~/venv/lib/python2.7/site-packages'))
exec(compile(open(os.path.join(os.getcwd(), 'run_client.py')).read(), os.path.join(os.getcwd(), 'run_client.py'), 'exec'))
