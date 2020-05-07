import os
import tempfile

version = "1.3.0"
cache = os.path.join(tempfile.gettempdir(), "icemet")
os.makedirs(cache, exist_ok=True)
