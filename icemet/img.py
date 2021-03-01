from icemet.file import File

import cv2
import numpy as np

import os

class Image(File):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.mat = kwargs.get("mat", None)
	
	def open(self, path):
		self.mat = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
	
	def save(self, path):
		root = os.path.split(path)[0]
		os.makedirs(root, exist_ok=True)
		cv2.imwrite(path, self.mat)
	
	def dynrange(self):
		return np.ptp(self.mat)
	
	def rotate(self, rot):
		return np.rot90(self.mat, k=int(rot/-90))

class BGSubStack:
	def __init__(self, len):
		if len < 3 or len % 2 == 0:
			raise ValueError("Invalid BGSubStack length")
		self.len = len
		self.full = False
		self.idx = 0
		self.means = np.empty((self.len,), dtype=np.float32)
		self.images = self.len * [None]
		self.stack = None
		self.eps = np.finfo(np.float32).eps
	
	def middle(self):
		return (self.idx + self.len//2) % self.len
	
	def current(self):
		return self.images[self.middle()]
	
	def push(self, img):
		if self.stack is None:
			self.stack = np.empty((self.len, *img.mat.shape), dtype=np.float32)
		
		self.means[self.idx] = np.mean(img.mat)
		self.images[self.idx] = img
		self.idx += 1
		if self.idx >= self.len:
			self.idx = 0
			self.full = True
		return self.full
	
	def meddiv(self):
		if not self.full:
			return None
		
		j = self.middle()
		for i in range(self.len):
			mi = self.means[i] + self.eps
			self.stack[i] = self.images[i].mat / mi * self.means[j]
		
		med = np.median(self.stack, axis=0) + self.eps
		mat = self.stack[j] / med * self.means[j]
		mat = np.clip(mat, a_min=0, a_max=255).astype(np.uint8)
		
		img = Image(mat=mat)
		img.set_name(self.images[j].name())
		return img
