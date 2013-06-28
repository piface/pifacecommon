import sys
import subprocess
from distutils.core import setup


# change this to True if you just want to install the module by itself
MODULE_ONLY = False

SCRIPT_ROOT = "https://raw.github.com/piface/pifacecommon/master/bin/"
UNBLACKLIST_SPI_CMD = \
    "curl {}unblacklist-spi-bcm2708.sh | bash".format(SCRIPT_ROOT)
SETUP_SPI_CMD = "curl {}spidev-setup.sh | bash".format(SCRIPT_ROOT)
SETUP_GPIO_CMD = "curl {}gpio-setup.sh | bash".format(SCRIPT_ROOT)


class InstallFailed(Exception):
    pass


def run_cmd(cmd, error_msg):
    success = subprocess.call([cmd], shell=True)
    if success != 0:
        raise InstallFailed(error_msg)


def unblacklist_spi_bcm2708():
    run_cmd(UNBLACKLIST_SPI_CMD, "Could not unblacklist spi_bcm2708.")


def setup_spi():
    unblacklist_spi_bcm2708()
    run_cmd(SETUP_SPI_CMD, "Could not set up SPI.")


def setup_gpio():
    run_cmd(SETUP_GPIO_CMD, "Could not set up GPIO.")


# Install everything: sudo python3 setup.py install
# Install module only: sudo python3 setup.py install module_only
if "install" in sys.argv and not MODULE_ONLY:
    try:
        setup_spi()
        setup_gpio()
    except IOError as e:
        if (e[0] == errno.EPERM):
            sys.stderr.write("Install script must be run as root.")
            sys.exit(1)


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
