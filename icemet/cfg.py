import yaml

class ConfigException(Exception):
	pass

class Config:
	def __init__(self, fn):
		self.file = fn
		self.dict = {}
		self.read(fn)
	
	def __setitem__(self, key, val):
		self.dict[key] = val
	
	def __getitem__(self, key):
		if not key in self.dict:
			raise ConfigException("Key not found '{}'".format(key))
		return self.dict[key]
	
	def get(self, key, default=None):
		return self.dict.get(key, default)
	
	def read(self, fn):
		try:
			with open(fn, "r") as fp:
				self.dict = yaml.load(fp, Loader=yaml.Loader)
		except Exception as e:
			raise ConfigException("Couldn't parse config file '{}'\n{}".format(fn, e))
	
	def write(self, fn):
		with open(fn, "w") as fp:
			yaml.dump(self.dict, fp, Dumper=yaml.Dumper)
