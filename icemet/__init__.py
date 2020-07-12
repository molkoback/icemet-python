import atexit
import os
import shutil
import tempfile

version = "1.5.0-dev"
cache = os.path.join(tempfile.gettempdir(), "icemet")

os.makedirs(cache, exist_ok=True)
atexit.register(lambda : shutil.rmtree(cache))
