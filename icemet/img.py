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
		self.len = len
		self.full = False
		self.i = 0
		self.means = np.empty((self.len,), dtype=np.float32)
		self.images = self.len * [None]
		self.stack = None
	
	def push(self, img):
		if self.stack is None:
			self.stack = np.empty((self.len, *img.mat.shape), dtype=np.float32)
		
		self.means[self.i] = np.mean(img.mat)
		self.images[self.i] = img
		self.i += 1
		if self.i >= self.len:
			self.i = 0
			self.full = True
		return self.full
	
	def meddiv(self):
		if not self.full:
			return None
		
		j = (self.i + self.len//2) % self.len
		for i in range(self.len):
			self.stack[i] = self.images[i].mat / self.means[i] * self.means[j]
		
		med = np.median(self.stack, axis=0) + 0.001
		mat = self.stack[j] / med * self.means[j]
		mat = np.clip(mat, a_min=0, a_max=255).astype(np.uint8)
		
		img = Image(mat=mat)
		img.set_name(self.images[j].name())
		return img
