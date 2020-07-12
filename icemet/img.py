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
	def __init__(self, len, size):
		self.len = len
		self.size = size
		self.clear()
	
	def clear(self):
		self.full = False
		self.i = 0
		self.stack = np.zeros((self.len, self.size[1], self.size[0]), dtype=np.uint8)
		self.images = self.len * [None]
	
	def push(self, img):
		self.stack[self.i] = img.mat
		self.images[self.i] = img
		self.i += 1
		if self.i >= self.len:
			self.i = 0
			self.full = True
	
	def meddiv(self):
		j = (self.i + self.len//2) % self.len
		med = np.median(self.stack, axis=0) + 0.001
		mat = self.stack[j] / med * np.mean(self.stack[j])
		mat = np.clip(mat, a_min=0, a_max=255).astype(np.uint8)
		
		img = self.images[j]
		img.mat = mat
		return img
