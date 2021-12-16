from icemet.file import File, FileStatus
from icemet.img import Image

import cv2

import json
import os
import shutil
import tempfile
import uuid
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

class ICEMETPackage1(Package):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.cache = kwargs.get("cache", os.path.join(tempfile.gettempdir(), "icemet"))
		self.fourcc = kwargs.get("fourcc", "FFV1")
		self.format = kwargs.get("format", "avi")
		self.quality = kwargs.get("quality", 100)
		
		self._dir = os.path.join(self.cache, ".icemet-"+uuid.uuid4().hex)
		self._vid_file = os.path.join(self._dir, "images." + self.format)
		self._data_file = os.path.join(self._dir, "data.json")
		self._file = os.path.join(self._dir, "package.zip")
		
		self._vid = None
		
		os.makedirs(self._dir)
	
	def __del__(self):
		shutil.rmtree(self._dir, ignore_errors=True)
	
	def _create_video(self, img):
		size = (img.mat.shape[-1], img.mat.shape[-2])
		self._vid = cv2.VideoWriter(self._vid_file, cv2.VideoWriter_fourcc(*self.fourcc), self.fps, size, False)
		self._vid.set(cv2.VIDEOWRITER_PROP_QUALITY, self.quality)
	
	def add_img(self, img):
		super().add_img(img)
		if img.status == FileStatus.NOTEMPTY:
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
	"icemet1": ([".ip1", ".iv1"], ICEMETPackage1),
}
packages["icemet"] = packages["icemet1"]

def ext2name(ext):
	for name, param in packages.items():
		for _ext in param[0]:
			if _ext == ext:
				return name
	return None

def name2ext(name):
	param = packages.get(name, None)
	if param is None:
		return None
	return param[0][0]

def create_package(name, **kwargs):
	param = packages.get(name, None)
	if param is None:
		raise PackageException("Invalid package format '{}'".format(name))
	return param[1](**kwargs)
