from icemet import cache
from icemet.file import File

import cv2

import json
import os
import shutil
import tempfile
import time
import zipfile

class PackageException(Exception):
	pass

class Package:
	def __init__(self, **kwargs):
		self.fps = kwargs.get("fps", 0)
		self.len = kwargs.get("len", 0)
		self.meas = kwargs.get("meas", {})
		self.files = kwargs.get("files", [])
	
	def add_file(self, f: File) -> None:
		self.files.append(f)
	
	def save(self, path: str) -> None:
		raise NotImplementedError()

class ICEMETV1Package(Package):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self._fourcc = "FFV1"
		
		self._dir = os.path.join(cache, str(round(time.time()*1000)))
		self._vid_file = os.path.join(self._dir, "files.avi")
		self._data_file = os.path.join(self._dir, "data.json")
		self._file = os.path.join(self._dir, "package.zip")
		os.makedirs(self._dir)
		
		self._vid = None
	
	def __del__(self):
		shutil.rmtree(self._dir)
	
	def _create_video(self, f):
		size = (f.image.shape[-1], f.image.shape[-2])
		self._vid = cv2.VideoWriter(self._vid_file, cv2.VideoWriter_fourcc(*self._fourcc), self.fps, size, False)
		self._vid.set(cv2.VIDEOWRITER_PROP_QUALITY, 100)
	
	def add_file(self, f):
		super().add_file(f)
		if self._vid is None:
			self._create_video(f)
		self._vid.write(f.image)
	
	def save(self, path):
		self._vid.release()
		
		data = {
			"fps": self.fps,
			"len": self.len,
			"meas": self.meas,
			"files": [f.name for f in self.files]
		}
		with open(self._data_file, "w") as fp:
			json.dump(data, fp)
		
		with zipfile.ZipFile(self._file, "w") as zf:
			zf.write(self._vid_file, os.path.basename(self._vid_file))
			zf.write(self._data_file, os.path.basename(self._data_file))
		
		shutil.move(self._file, path)

packages = {
	"icemet_v1": (".iv1", ICEMETV1Package),
}
packages["icemet"] = packages["icemet_v1"]

def ext2name(ext):
	list = [k for k, v in packages.items() if v[0] == ext]
	if list:
		return list[0]
	return ""

def name2ext(name):
	if not name in packages:
		return ""
	return packages[name][0]

def create_package(name, **kwargs):
	if not name in packages:
		raise PackageException("Invalid package format '{}'".format(name))
	return packages[name][1](**kwargs)
