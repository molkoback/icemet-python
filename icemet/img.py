from icemet.file import File

import cv2
import numpy as np
import torch
import torchvision.transforms.functional as tf
from torchvision.transforms import InterpolationMode

from collections import deque
import os

class ImageException(Exception):
	pass

class Image(File):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.data = kwargs.get("data", None)
		if not self.data is None:
			self.set_data(self.data)
		
		self.params = kwargs.get("params", {})
	
	def set_data(self, data):
		if isinstance(data, np.ndarray):
			data = torch.from_numpy(data)
		elif not isinstance(data, torch.Tensor):
			raise ValueError("Invalid image data type")
		self.data = data.to(torch.get_default_device()).type(torch.float32)
	
	def tensor(self):
		if self.data is None:
			None
		return self.data
	
	def numpy(self, uint8=False):
		if self.data is None:
			return None
		mat = self.tensor().to("cpu").numpy()
		if uint8:
			mat = mat.clip(0, 255).astype(np.uint8)
		return mat
	
	def open(self, path):
		data = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
		self.set_data(data)
	
	def save(self, path):
		root = os.path.split(path)[0]
		if root:
			os.makedirs(root, exist_ok=True)
		cv2.imwrite(path, self.numpy(uint8=True))
	
	def dynrange(self):
		if not "dynrange" in self.params:
			self.params["dynrange"] = (self.tensor().max() - self.max.min()).item()
		return self.params["dynrange"]
	
	def mean(self):
		if not "mean" in self.params:
			self.params["mean"] = self.tensor().mean().item()
		return self.params["mean"]
	
	def median(self):
		if not "median" in self.params:
			self.params["median"] = self.tensor().median().item()
		return self.params["median"]
	
	def _squeeze(self, t):
		return t.squeeze(0).squeeze(0)
	
	def _unsqueeze(self, t):
		return t.unsqueeze(0).unsqueeze(0)
	
	def crop(self, x, y, w, h):
		self.data = self._unsqueeze(self.data)
		self.data = tf.crop(self.data, y, x, h, w)
		self.data = self._squeeze(self.data)
	
	def scale(self, w, h):
		self.data = self._unsqueeze(self.data)
		self.data = tf.resize(
			self.data,
			(h, w),
			interpolation=InterpolationMode.BICUBIC,
			antialias=True
		)
		self.data = self._squeeze(self.data)
	
	def rotate(self, angle):
		self.data = self._unsqueeze(self.data)
		self.data = tf.rotate(self.data, angle)
		self.data = self._squeeze(self.data)
	
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
		return super().push(img)
	
	def combine(self):
		if not self.full():
			return None
		
		img_curr = self.current()
		t = torch.zeros(img_curr.tensor().size(), dtype=torch.float32)
		t.to(torch.get_default_device())
		sum = 0
		for img in self.images:
			mean = img.mean()
			t = t + (img.tensor() - mean)
			sum += mean
		t = t + sum / len(self.images)
		
		img = Image()
		img.set_name(img_curr.name())
		img.data = t
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
		if self.stack is None:
			self.stack = (
				torch.empty((self.len, *img.tensor().size()), dtype=torch.float32)
				.to(torch.get_default_device())
			)
		return super().push(img)
	
	def meddiv(self):
		if not self.full():
			return None
		
		img_curr = self.current()
		for i, img in enumerate(self.images):
			self.stack[i] = img.tensor() / img.mean() * img_curr.mean()
		
		med = self.stack.median(dim=0).values
		t = img_curr.tensor() / med * img_curr.mean()
		t = t.nan_to_num(nan=0.0)
		
		img = Image()
		img.set_name(img_curr.name())
		img.data = t
		return img
