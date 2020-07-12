import enum
from datetime import datetime
import os

class FileException(Exception):
	pass

class FileStatus(enum.Enum):
	NONE = "X"
	NOTEMPTY = "T"
	EMPTY = "F"
	SKIP = "S"

class File:
	def __init__(self, **kwargs):
		self.sensor_id = kwargs.get("sensor_id", 0)
		self.datetime = kwargs.get("datetime", datetime.now())
		self.frame = kwargs.get("frame", 0)
		self.sub = kwargs.get("sub", 0)
		self.status = kwargs.get("status", FileStatus.NONE)
		self.name_formats = {
			"file_v1": (self._get_name_filev1, self._set_name_filev1)
		}
	
	def __repr__(self):
		return "<File {}>".format(self.name())
	
	def __str__(self):
		return self.name()
	
	def __eq__(self, other):
		return (
			self.sensor_id == other.sensor_id and
			self.datetime == other.datetime and
			self.frame == other.frame
		)
	
	def __ne__(self, other):
		return not self.__eq__(other)
	
	def __lt__(self, other):
		return (
			(self.sensor_id<other.sensor_id) or
			(self.sensor_id==other.sensor_id and self.datetime<other.datetime) or
			(self.sensor_id==other.sensor_id and self.datetime==other.datetime and self.frame<other.frame)
		)
	
	def __le__(self, other):
		return self.__eq__(other) or self.__lt__(other)
	
	def __gt__(self, other):
		return not self.__le__(other)
	
	def __ge__(self, other):
		return not self.__lt__(other)
	
	def _get_name_filev1(self):
		end = "_{:d}".format(self.sub) if self.sub > 0 else ""
		return "{:02X}_{:02d}{:02d}{:02d}_{:02d}{:02d}{:02d}{:03d}_{:06d}_{}{}".format(
			self.sensor_id % 0xff,
			self.datetime.day, self.datetime.month, self.datetime.year%100,
			self.datetime.hour, self.datetime.minute, self.datetime.second, self.datetime.microsecond//1000,
			self.frame%1000000,
			self.status.value,
			end
		)
	
	def _set_name_filev1(self, name):
		try:
			if name.count("_") < 4:
				raise Exception()
			self.sensor_id = int(name[0:2], 16)
			self.datetime = datetime(
				year=int(name[7:9])+2000,
				month=int(name[5:7]),
				day=int(name[3:5]),
				hour=int(name[10:12]), 
				minute=int(name[12:14]), 
				second=int(name[14:16]),
				microsecond=int(name[16:19])*1000
			)
			self.frame = int(name[20:26])
			self.status = FileStatus(name[27])
			self.sub = int(name[29:]) if len(name) > 28 else 0
		except:
			raise FileException("Invalid file name")
	
	def name(self, fmt="file_v1"):
		return self.name_formats[fmt][0]()
	
	def set_name(self, name, fmt="file_v1"):
		self.name_formats[fmt][1](name)
	
	def path(self, root=".", ext=".png", subdirs=True):
		if not ext.startswith("."):
			ext = "." + ext
		if subdirs:
			root = os.path.join(
				root,
				"{:04d}-{:02d}".format(self.datetime.year, self.datetime.month),
				"{:02d}".format(self.datetime.day),
				"{:02d}".format(self.datetime.hour)
			)
		return os.path.join(root, self.name() + ext)
	
	@classmethod
	def frompath(cls, path):
		try:
			obj = cls()
			name = os.path.splitext(os.path.split(path)[-1])[0]
			for fmt in obj.name_formats.keys():
				try:
					obj.set_name(name, fmt=fmt)
					return obj
				except:
					pass
			raise Exception()
		except:
			raise FileException("Invalid file path")
