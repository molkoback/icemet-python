import math

ice_classes = {
	"R1": 500,
	"R2": 900,
	"R3": 1600,
	"R4": 2800,
	"R5": 5000,
	"R6": 8900,
	"R7": 16000,
	"R8": 28000,
	"R9": 50000
}

def density_air(p, T, R=287.058):
	TK = T + 273.15
	return p / (R * TK)

def viscosity_air(T):
	# Sutherland model
	TK = T + 273.15
	return 1.459e-6 * math.pow(TK, 1.5) / (TK+109.1)

def reynoldsnum(rho_air, d, v, mu_air):
	return (rho_air * d * v) / mu_air

def icingrate(eta1, eta2, eta3, w, A, v):
	return eta1 * eta2 * eta3 * w * A * v

class IcingObjectExeption(Exception):
	pass

class IcingObject:
	def icingrate(self, LWC, MVD, T, v, **kwargs) -> float:
		raise NotImplementedError()

class Cylinder(IcingObject):
	def __init__(self, D, l):
		self.D = D
		self.l = l
		self.A = D * l
	
	@staticmethod
	def K(rho_water, MVD, v, mu_air, D):
		return rho_water * math.pow(MVD, 2) * v / (9 * mu_air * D)
	
	@staticmethod
	def phi(Re, K):
		if K == 0:
			return 0
		return math.pow(Re, 2) / K
	
	@staticmethod
	def eta1(K, phi):
		try:
			A = 1.066 * math.pow(K, -0.00616) * math.exp(-1.103 * math.pow(K, -0.688))
			B = 3.641 * math.pow(K, -0.498) * math.exp(-1.497 * math.pow(K, -0.694))
			C = 0.00637 * math.pow(phi - 100, 0.381)
			val = A - 0.028 - C*(B-0.0454)
		except:
			return 0
		return max(val, 0)
	
	def icingrate(self, LWC, MVD, T, v, p=101325, T_max=2.0):
		if T >= T_max:
			return 0.0
		
		rho_air = density_air(p, T)
		mu_air = viscosity_air(T)
		rho_water = 1000.0
		Re = reynoldsnum(rho_air, MVD, v, mu_air)
		K = self.K(rho_water, MVD, v, mu_air, self.D)
		phi = self.phi(Re, K)
		eta1 = self.eta1(K, phi)
		eta2 = 1.0
		eta3 = 1.0
		return icingrate(eta1, eta2, eta3, LWC, self.A, v)

class Event:
	def __init__(self, accretion=0.0):
		self.accretion = accretion
		self.start = None
		self.end = None
		self._rate_prev = None
		self._time_prev = None
	
	def append(self, rate, dt):
		if self.start == None:
			self.start = dt
		self.end = dt
		
		time = dt.timestamp()
		if not self._rate_prev is None:
			self.accretion += self._rate_prev * (time - self._time_prev)
		self._rate_prev = rate
		self._time_prev = time
	
	def ice_class(self):
		cls = None
		for k, v in ice_classes.items():
			if self.accretion > v:
				cls = k
			else:
				return cls
