import os

class PackageException(Exception):
	pass

def _save_icemet_v1(path, pkg):
	raise NotImplementedError()

_packages = {
	"icemet": (".iv1", _save_icemet_v1),
	"icemet_v1": (".iv1", _save_icemet_v1)
}

def ext2name(ext):
	list = [k for k, v in _packages.items() if v[0] == ext]
	if list:
		return list[0]
	return ""

def name2ext(name):
	if not name in _packages:
		return ""
	return _packages[name][0]

class Package:
	def __init__(self, **kwargs):
		self.fps = kwargs.get("fps", 0)
		self.len = kwargs.get("len", 0)
		self.files = kwargs.get("files", [])
		self.meas = kwargs.get("meas", {})
	
	def save(self, path):
		ext = os.path.splitext(path)[1]
		name = ext2name(ext)
		if not name:
			raise PackageException("Invalid package extension '{}'".format(ext))
		_packages[name][1](path, self)
