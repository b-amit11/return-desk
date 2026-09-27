"""Public hosting entrypoint: live AI is disabled even if a key exists."""
import os
import runpy
from pathlib import Path
os.environ['RETURNDESK_PUBLIC_DEMO']='1'
runpy.run_path(str(Path(__file__).with_name('app.py')),run_name='__main__')
