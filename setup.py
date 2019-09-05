# -*- coding: utf-8 -*-
from os.path import join, dirname

from setuptools import setup, find_packages

f = open(join(dirname(__file__), 'README.rst'))
long_description = f.read().strip()
f.close()

install_requires = [
  'requests>=2.4.3',
  'python-dateutil>=2.2',
  'typing'
]

setup(
  name='python-openhab',
  description="python library for accessing the openHAB REST API",
  license="AGPLv3+",
  url="https://github.com/sim0nx/python-openhab",
  download_url="https://github.com/sim0nx/python-openhab",
  long_description=long_description,
  version='2.10.0',
  author="Georges Toth",
  author_email="georges@trypill.org",
  packages=find_packages(
    where='.',
  ),
  keywords=['openhab'],
  classifiers=[
    "Development Status :: 4 - Beta",
    "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
    "Intended Audience :: Developers",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3 :: Only",
  ],
  install_requires=install_requires,
)
