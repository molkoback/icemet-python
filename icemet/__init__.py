import atexit
import os
import shutil
import tempfile
import time

version = "1.5.4"
cache = os.path.join(tempfile.gettempdir(), "icemet", "{:x}".format(int(time.time()*1000)))

os.makedirs(cache)
atexit.register(lambda : shutil.rmtree(cache, ignore_errors=True))
