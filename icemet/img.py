from icemet.file import File

import cv2
import numpy as np

from collections import deque
import os

class Image(File):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.mat = kwargs.get("mat", None)
		self.params = kwargs.get("params", {})
	
	def open(self, path):
		self.mat = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
	
	def save(self, path):
		root = os.path.split(path)[0]
		os.makedirs(root, exist_ok=True)
		cv2.imwrite(path, self.mat)
	
	def dynrange(self):
		if not "dynrange" in self.params:
			self.params["dynrange"] = np.ptp(self.mat)
		return self.params["dynrange"]
	
	def mean(self):
		if not "mean" in self.params:
			self.params["mean"] = np.mean(self.mat)
		return self.params["mean"]
	
	def median(self):
		if not "median" in self.params:
			self.params["median"] = np.median(self.mat)
		return self.params["median"]
	
	def rotate(self, rot):
		return np.rot90(self.mat, k=int(rot/-90))
	
	@classmethod
	def frompath(cls, path):
		obj = cls()
		obj.set_name(os.path.splitext(os.path.split(path)[-1])[0])
		obj.open(path)
		return obj

class ImageStack:
	def __init__(self, len):
		self.len = len
		self.images = deque(maxlen=len)
	
	def index(self):
		return len(self.images) - 1
	
	def current(self):
		return self.images[self.index()]
	
	def full(self):
		return len(self.images) == self.len
	
	def push(self, img):
		self.images.append(img)
		return self.full()

class CombineStack(ImageStack):
	def __init__(self, len):
		super().__init__(len)
	
	def push(self, img):
		img.mean() # Save mean
		return super().push(img)
	
	def combine(self):
		if not self.full():
			return None
		
		img_curr = self.current()
		mat = np.full(img_curr.mat.shape, img_curr.mean(), dtype=np.float32)
		for img in self.images:
			mat = mat + (img.mat.astype(np.float32) - img.mean())
		mat = np.clip(mat, 0, 255).astype(np.uint8)
		
		img = Image(mat=mat)
		img.set_name(img_curr.name())
		return img

class BGSubStack(ImageStack):
	def __init__(self, len, use_middle=True):
		super().__init__(len)
		self.use_middle = use_middle
		if len < 2 or (use_middle and (len < 3 or len % 2 == 0)):
			raise ValueError("Invalid BGSubStack length")
		self.stack = None
	
	def index(self):
		l = len(self.images)
		return l//2 if self.use_middle else l-1
	
	def push(self, img):
		img.mean() # Save mean
		if self.stack is None:
			self.stack = np.empty((self.len, *img.mat.shape), dtype=np.float32)
		return super().push(img)
	
	def meddiv(self):
		if not self.full():
			return None
		
		img_curr = self.current()
		eps = np.finfo(np.float32).eps
		for i, img in enumerate(self.images):
			self.stack[i] = img.mat / img.mean() * img_curr.mean()
		
		med = np.median(self.stack, axis=0) + eps
		mat = img_curr.mat / med * img_curr.mean()
		mat = np.clip(mat, a_min=0, a_max=255).astype(np.uint8)
		
		img = Image(mat=mat)
		img.set_name(img_curr.name())
		return img
