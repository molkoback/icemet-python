import cv2
import numpy as np

import os

class BGSubStack:
	def __init__(self, len, size):
		self.len = len
		self.size = size
		self.clear()
	
	def clear(self):
		self.full = False
		self.i = 0
		self.images = np.zeros((self.len, self.size[1], self.size[0]), dtype=np.uint8)
	
	def push(self, im):
		self.images[self.i] = im
		self.i += 1
		if self.i >= self.len:
			self.i = 0
			self.full = True
	
	def meddiv(self):
		j = (self.i + self.len//2) % self.len
		im = self.images[j] / np.median(self.images, axis=0) * np.mean(self.images[j])
		return im.astype(np.uint8)

def open_image(path):
	return cv2.imread(path, cv2.IMREAD_GRAYSCALE)

def save_image(path, im):
	root = os.path.split(path)[0]
	if not os.path.exists(root):
		os.makedirs(root)
	cv2.imwrite(path, im)

def dynrange(im):
	return np.ptp(im)

def rotate(im, rot):
	return np.rot90(im, k=int(rot/-90))
