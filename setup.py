# -*- coding: utf-8 -*-
from os.path import join, dirname

import setuptools

f = open(join(dirname(__file__), 'README.rst'))
long_description = f.read().strip()
f.close()

setuptools.setup(
  name='python-openhab',
  description="python library for accessing the openHAB REST API",
  license="AGPLv3+",
  url="https://github.com/sim0nx/python-openhab",
  download_url="https://github.com/sim0nx/python-openhab",
  long_description=long_description,
  version='2.11.2',
  author="Georges Toth",
  author_email="georges@trypill.org",
  packages=setuptools.find_packages(),
  package_data={'openhab': ['py.typed']},
  keywords=['openHAB'],
  classifiers=[
    "Development Status :: 4 - Beta",
    "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
    "Intended Audience :: Developers",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3 :: Only",
  ],
  install_requires=[
    'requests>=2.4.3',
    'python-dateutil>=2.2',
  ],
  python_requires='>=3.5',
)
