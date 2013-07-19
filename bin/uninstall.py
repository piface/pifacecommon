import os
import sys
import shutil
import subprocess


ANSWERS = ('yes', 'y', '')

PY3 = sys.version_info.major >= 3
if not PY3:
    input = raw_input


def get_version():
    if PY3:
        version_vars = {}
        with open(VERSION_FILE) as f:
            code = compile(f.read(), VERSION_FILE, 'exec')
            exec(code, None, version_vars)
        return version_vars['__version__']
    else:
        execfile(VERSION_FILE)
        return __version__


DIST_PACKAGES = "/usr/local/lib/python{major}.{minor}/dist-packages/".format(
    major=sys.version_info.major, minor=sys.version_info.minor)
PIFACE_COMMON_PACKAGE_DIR = DIST_PACKAGES + "pifacecommon/"
VERSION_FILE = 'pifacecommon/version.py'
PIFACE_COMMON_EGG_INFO = \
    DIST_PACKAGES + "pifacecommon-{version}.egg-info".format(
        version=get_version())

# get scripts from github
# SCRIPT_ROOT = "https://raw.github.com/piface/pifacecommon/master/bin/"
# BLACKLIST_SPI_CMD = \
#     "curl {}blacklist-spi-bcm2708.sh | bash".format(SCRIPT_ROOT)
# TEARDOWN_SPI_CMD = "curl {}spidev-teardown.sh | bash".format(SCRIPT_ROOT)
# TEARDOWN_GPIO_CMD = "curl {}gpio-teardown.sh | bash".format(SCRIPT_ROOT)

# get scripts from local bin/
BLACKLIST_SPI_CMD = "bin/blacklist-spi-bcm2708.sh"
TEARDOWN_SPI_CMD = "bin/spidev-teardown.sh"
TEARDOWN_GPIO_CMD = "bin/gpio-teardown.sh"


class UninstallFailed(Exception):
    pass


def run_cmd(cmd, error_msg):
    success = subprocess.call([cmd], shell=True)
    if success != 0:
        raise UninstallFailed(error_msg)


def blacklist_spi_bcm2708():
    print("Blacklisting SPI module.")
    run_cmd(BLACKLIST_SPI_CMD, "Could not unblacklist spi_bcm2708.")


def remove_gpio_udev_rule_and_group():
    print("Removing GPIO udev rule and group.")
    run_cmd(TEARDOWN_GPIO_CMD, "Could not tear down GPIO.")


def remove_spi_udev_rule_and_group():
    print("Removing SPI udev rule and group.")
    run_cmd(TEARDOWN_SPI_CMD, "Could not tear down SPI.")


def remove_files():
    print("Removing files.")
    shutil.rmtree(PIFACE_COMMON_PACKAGE_DIR)
    os.remove(PIFACE_COMMON_EGG_INFO)


def ask_question(question):
    return input("{} [Y/n] ".format(question)).lower() in ANSWERS


if __name__ == '__main__':
    yes_to_all = '-y' in sys.argv
    no_to_all = '-n' in sys.argv

    if no_to_all and yes_to_all:
        print("Can't say yes and no to all!")
        sys.exit(1)

    if not no_to_all:
        if yes_to_all or ask_question(
                "Would you like to blacklist the SPI module (spi-bcm2708)?"):
            blacklist_spi_bcm2708()

        if yes_to_all or ask_question(
                "Would you like to remove the SPI udev rule and group?"):
            remove_spi_udev_rule_and_group()

        if yes_to_all or ask_question(
                "Would you like to remove the GPIO udev rule and group?"):
            remove_gpio_udev_rule_and_group()

    remove_files()
