from icemet import __version__

from setuptools import setup, find_packages

with open("README.md") as fp:
	readme = fp.read()

with open("requirements.txt") as fp:
	requirements = fp.read().splitlines()

setup(
	name="icemet-python",
	version=__version__,
	packages=find_packages(),
	
	install_requires=requirements,
	
	author="Eero Molkoselkä",
	author_email="eero.molkoselka@gmail.com",
	description="ICEMET Python libraries",
	long_description=readme,
	url="https://github.com/molkoback/icemet-python",
	license="MIT",
	
	classifiers=[
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
		"Programming Language :: Python :: 3",
		"Topic :: Scientific/Engineering :: Atmospheric Science",
	]
)
