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
		self.size = 0, 0
		self.fps = kwargs.get("fps", 0)
		self.len = kwargs.get("len", 0)
		self.meas = kwargs.get("meas", {})
		self.images = kwargs.get("images", [])
	
	def add_img(self, img: Image) -> None:
		if not self.images:
			self.size = img.mat.shape[1], img.mat.shape[0]
		self.images.append(img)
	
	def save(self, path: str) -> None:
		raise NotImplementedError()

class DummyPackage(Package):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
	
	def save(self, path: str) -> None:
		pass

class ImageWriter:
	def write(self, img: Image) -> None:
		raise NotImplementedError()
	
	def close(self) -> None:
		raise NotImplementedError()

class VideoWriter(ImageWriter):
	def __init__(self, file, size, fps, fourcc, format, quality):
		self._vid = cv2.VideoWriter(file, cv2.VideoWriter_fourcc(*fourcc), fps, size, False)
		self._vid.set(cv2.VIDEOWRITER_PROP_QUALITY, quality)
	
	def write(self, img):
		self._vid.write(img.mat)
	
	def close(self):
		self._vid.release()

class BinaryWriter(ImageWriter):
	def __init__(self, file):
		self._fp = open(file, "wb")
	
	def write(self, img):
		self._fp.write(img.mat.data)
	
	def close(self):
		self._fp.close()

class ICEMETPackage1(Package):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.raw = kwargs.get("raw", False)
		self.cache = kwargs.get("cache", os.path.join(tempfile.gettempdir(), "icemet"))
		self.fourcc = kwargs.get("fourcc", "FFV1")
		if self.raw:
			self.format = "bin"
		else:
			self.format = kwargs.get("format", "avi")
		self.quality = kwargs.get("quality", 100)
		
		self._dir = os.path.join(self.cache, ".icemet-"+uuid.uuid4().hex)
		self._images_file = os.path.join(self._dir, "images." + self.format)
		self._data_file = os.path.join(self._dir, "data.json")
		self._file = os.path.join(self._dir, "package.zip")
		
		self._writer = None
		
		os.makedirs(self._dir)
	
	def __del__(self):
		shutil.rmtree(self._dir, ignore_errors=True)
	
	def _create_writer(self):
		if self.raw:
			return BinaryWriter(self._images_file)
		return VideoWriter(self._images_file, self.size, self.fps, self.fourcc, self.format, self.quality)
	
	def add_img(self, img):
		super().add_img(img)
		if img.status == FileStatus.NOTEMPTY:
			if self._writer is None:
				self._writer = self._create_writer()
			self._writer.write(img)
	
	def save(self, path):
		data = {
			"size": self.size,
			"fps": self.fps,
			"len": self.len,
			"meas": self.meas,
			"images": [img.name() for img in self.images]
		}
		with open(self._data_file, "w") as fp:
			json.dump(data, fp)
		
		with zipfile.ZipFile(self._file, "w", compression=zipfile.ZIP_STORED) as zf:
			zf.write(self._data_file, os.path.basename(self._data_file))
			if not self._writer is None:
				self._writer.close()
				zf.write(self._images_file, os.path.basename(self._images_file))
		
		shutil.move(self._file, path)

packages = {
	"dummy": ([".dummy"], DummyPackage),
	"icemet1": ([".ip1", ".iv1"], ICEMETPackage1)
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
