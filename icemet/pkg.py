from icemet import cache
from icemet.file import File
from icemet.img import Image

import cv2

import json
import os
import shutil
import tempfile
import time
import zipfile

class PackageException(Exception):
	pass

class Package(File):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.fps = kwargs.get("fps", 0)
		self.len = kwargs.get("len", 0)
		self.meas = kwargs.get("meas", {})
		self.images = kwargs.get("images", [])
	
	def add_img(self, img: Image) -> None:
		self.images.append(img)
	
	def save(self, path: str) -> None:
		raise NotImplementedError()

class ICEMETV1Package(Package):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self._fourcc = "FFV1"
		
		self._dir = os.path.join(cache, str(round(time.time()*1000)))
		self._vid_file = os.path.join(self._dir, "images.avi")
		self._data_file = os.path.join(self._dir, "data.json")
		self._file = os.path.join(self._dir, "package.zip")
		os.makedirs(self._dir)
		
		self._vid = None
	
	def __del__(self):
		shutil.rmtree(self._dir, ignore_errors=True)
	
	def _create_video(self, img):
		size = (img.mat.shape[-1], img.mat.shape[-2])
		self._vid = cv2.VideoWriter(self._vid_file, cv2.VideoWriter_fourcc(*self._fourcc), self.fps, size, False)
		self._vid.set(cv2.VIDEOWRITER_PROP_QUALITY, 100)
	
	def add_img(self, img):
		super().add_img(img)
		if self._vid is None:
			self._create_video(img)
		self._vid.write(img.mat)
	
	def save(self, path):
		data = {
			"fps": self.fps,
			"len": self.len,
			"meas": self.meas,
			"images": [img.name() for img in self.images]
		}
		with open(self._data_file, "w") as fp:
			json.dump(data, fp)
		
		with zipfile.ZipFile(self._file, "w") as zf:
			zf.write(self._data_file, os.path.basename(self._data_file))
			if not self._vid is None:
				self._vid.release()
				zf.write(self._vid_file, os.path.basename(self._vid_file))
		
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
