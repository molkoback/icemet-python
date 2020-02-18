import yaml

class ConfigException(Exception):
	pass

class Config:
	def read(self, fn):
		with open(fn, "r") as fp:
			self.dict = yaml.load(fp, Loader=yaml.Loader)
	
	def write(self, fn):
		with open(fn, "w") as fp:
			yaml.dump(self.dict, fp, Dumper=yaml.Dumper)
