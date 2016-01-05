import sys
import os
import os.path

sys.path.insert(0, os.path.expanduser('~/venv/lib/python2.7/site-packages'))
execfile(os.path.join(os.getcwd(), 'run_client.py'))
