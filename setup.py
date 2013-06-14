#!/usr/bin/env python3

from setuptools import setup

setup(
    name='pifacecommon',
    version='1.0',
    description='The PiFace common functions module.',
    author='Thomas Preston',
    author_email='thomasmarkpreston@gmail.com',
    url='http://pi.cs.man.ac.uk/interface.htm',
    packages=['pifacecommon'],
    long_description="pifacecommon provides common classes, functions and"
        "variables to various piface related modules.",
    classifiers=[
        "License :: OSI Approved :: GNU Affero General Public License v3 or "
        "later (AGPLv3+)",
        "Programming Language :: Python",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords='piface raspberrypi openlx',
    license='GPLv3+',
    install_requires=[
        'setuptools',
    ],
)
