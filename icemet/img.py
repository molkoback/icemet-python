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
	
	def push(self, image):
		self.images[self.i] = image
		self.i += 1
		if self.i >= self.len:
			self.i = 0
			self.full = True
	
	def meddiv(self):
		j = (self.i + self.len//2) % self.len
		image = self.images[j] / np.median(self.images, axis=0) * np.mean(self.images[j])
		return image.astype(np.uint8)

def open_image(path):
	return cv2.imread(path, cv2.IMREAD_GRAYSCALE)

def save_image(path, image):
	root = os.path.split(path)[0]
	os.makedirs(root, exist_ok=True)
	cv2.imwrite(path, image)

def dynrange(image):
	return np.ptp(image)

def rotate(image, rot):
	return np.rot90(image, k=int(rot/-90))
