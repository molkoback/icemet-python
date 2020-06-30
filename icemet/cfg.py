import yaml

class ConfigException(Exception):
	pass

class Config:
	def __init__(self, fn):
		self.file = fn
		self.dict = {}
		self.read(fn)
	
	def __setitem__(self, k, v):
		self.dict[k] = v
	
	def __getitem__(self, k):
		return self.dict.get(k, None)
	
	def read(self, fn):
		try:
			with open(fn, "r") as fp:
				self.set_dict(yaml.load(fp, Loader=yaml.Loader))
		except Exception as e:
			raise ConfigException("Couldn't parse config file '{}'\n{}".format(fn, e))
	
	def write(self, fn):
		with open(fn, "w") as fp:
			yaml.dump(self.dict, fp, Dumper=yaml.Dumper)
	
	def set_dict(self, dict):
		self.dict = dict
