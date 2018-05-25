#!/usr/bin/env python
"""
Copyright 2018 Sigvald Marholm <marholm@marebakken.com>

This file is part of TaskTimer.

TaskTimer is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

TaskTimer is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with TaskTimer.  If not, see <http://www.gnu.org/licenses/>.
"""

from setuptools import setup

with open('README.rst', encoding='utf-8') as f:
    long_description = f.read()

setup(name='tasktimer',
      version='1.0.1',
      description='Indicates progress during runtime, while keeping track of time consumed by user-defined tasks.',
      long_description=long_description,
      author='Sigvald Marholm',
      author_email='marholm@marebakken.com',
      url='https://github.com/sigvaldm/tasktimer.git',
      py_modules=['tasktimer'],
      install_requires=['frmt >1,<2*dev*'],
      license='LGPL'
     )

