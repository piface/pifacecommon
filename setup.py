#!/usr/bin/env python3
from distutils.core import setup

DISTUTILS_DEBUG = True

setup(
    name='pifacecommon',
    version='1.0',
    description='The PiFace Common functions module.',
    author='Thomas Preston',
    author_email='thomasmarkpreston@gmail.com',
    license='GPLv3+',
    url='http://pi.cs.man.ac.uk/interface.htm',
    py_modules=['pifacecommon', 'asm_generic_ioctl'],
)
