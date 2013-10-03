import posix
import ctypes
from fcntl import ioctl
from .linux_spi_spidev import spi_ioc_transfer, SPI_IOC_MESSAGE


SPIDEV = '/dev/spidev'
SPI_HELP_LINK = "http://piface.github.io/pifacecommon/installation.html" \
    "#enable-the-spi-module"


class SPIInitError(Exception):
    pass


class SPIDevice(object):
    """An SPI Device at /dev/spi<bus>.<chip_select>."""
    def __init__(self, bus=0, chip_select=0, callback=None):
        """Initialises the SPI device file descriptor.

        :param bus: The SPI device bus number
        :type bus: int
        :param chip_select: The SPI device chip_select number
        :param chip_select: int
        :raises: InitError
        """
        self.bus = bus
        self.chip_select = chip_select
        self.callback = callback
        spi_device = "%s%d.%d" % (SPIDEV, self.bus, self.chip_select)
        try:
            self.fd = posix.open(spi_device, posix.O_RDWR)
        except OSError as e:
            raise SPIInitError(
                "I can't see %s. Have you enabled the SPI module? (%s)"
                % (spi_device, SPI_HELP_LINK)
            )  # from e  # from is only available in Python 3

    def __del__(self):
        posix.close(self.fd)
        del self.fd

    def spisend(self, bytes_to_send):
        """Sends bytes via the SPI bus.

        :param bytes_to_send: The bytes to send on the SPI device.
        :type bytes_to_send: bytes
        :returns: bytes -- returned bytes from SPI device
        :raises: InitError
        """
        # make some buffer space to store reading/writing
        wbuffer = ctypes.create_string_buffer(bytes_to_send,
                                              len(bytes_to_send))
        rbuffer = ctypes.create_string_buffer(len(bytes_to_send))

        # create the spi transfer struct
        transfer = spi_ioc_transfer(
            tx_buf=ctypes.addressof(wbuffer),
            rx_buf=ctypes.addressof(rbuffer),
            len=ctypes.sizeof(wbuffer)
        )

        if self.callback is not None:
            self.callback(bytes_to_send)
        # send the spi command
        ioctl(self.fd, SPI_IOC_MESSAGE(1), transfer)
        return ctypes.string_at(rbuffer, ctypes.sizeof(rbuffer))
