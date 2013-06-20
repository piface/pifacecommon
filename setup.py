from distutils.core import setup


setup(
    name='pifacecommon',
    version='1.1',
    description='The PiFace common functions module.',
    author='Thomas Preston',
    author_email='thomasmarkpreston@gmail.com',
    license='GPLv3+',
    url='https://github.com/piface/pifacecommon',
    packages=['pifacecommon'],
    long_description="pifacecommon provides common classes, functions and "
        "variables to various piface related modules.",
    classifiers=[
        "License :: OSI Approved :: GNU Affero General Public License v3 or "
        "later (AGPLv3+)",
        "Programming Language :: Python :: 3",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords='piface raspberrypi openlx',
)
