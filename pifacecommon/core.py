import sys
import ctypes
import posix
import time
from fcntl import ioctl
from .linux_spi_spidev import spi_ioc_transfer, SPI_IOC_MESSAGE


MAX_BOARDS = 4

WRITE_CMD = 0
READ_CMD = 1

# Register addresses
IODIRA = 0x0  # I/O direction A
IODIRB = 0x1  # I/O direction B
IPOLA = 0x2  # I/O polarity A
IPOLB = 0x3  # I/O polarity B
GPINTENA = 0x4  # interupt enable A
GPINTENB = 0x5  # interupt enable B
DEFVALA = 0x6  # register default value A (interupts)
DEFVALB = 0x7  # register default value B (interupts)
INTCONA = 0x8  # interupt control A
INTCONB = 0x9  # interupt control B
IOCON = 0xA  # I/O config (also 0xB)
GPPUA = 0xC  # port A pullups
GPPUB = 0xD  # port B pullups
INTFA = 0xE  # interupt flag A (where the interupt came from)
INTFB = 0xF  # interupt flag B
INTCAPA = 0x10  # interupt capture A (value at interupt is saved here)
INTCAPB = 0x11  # interupt capture B
GPIOA = 0x12  # port A
GPIOB = 0x13  # port B

# I/O config
BANK_OFF = 0x00  # addressing mode
BANK_ON = 0x80
INT_MIRROR_ON = 0x40  # interupt mirror (INTa|INTb)
INT_MIRROR_OFF = 0x00
SEQOP_OFF = 0x20  # incrementing address pointer
SEQOP_ON = 0x00
DISSLW_ON = 0x10  # slew rate
DISSLW_OFF = 0x00
HAEN_ON = 0x08  # hardware addressing
HAEN_OFF = 0x00
ODR_ON = 0x04  # open drain for interupts
ODR_OFF = 0x00
INTPOL_HIGH = 0x02  # interupt polarity
INTPOL_LOW = 0x00

SPIDEV = '/dev/spidev'
SPI_HELP_LINK = "http://piface.github.io/pifacecommon/installation.html" \
    "#enable-the-spi-module"

spidev_fd = None


class RangeError(Exception):
    pass


class InitError(Exception):
    pass


class InputDeviceError(Exception):
    pass


class DigitalPort(object):
    """A digital port on a PiFace product."""

    def __init__(self, port, board_num=0):
        self.port = port
        if board_num < 0 or board_num >= MAX_BOARDS:
            raise RangeError(
                "Specified board index (%d) out of range." % board_num
            )
        else:
            self.board_num = board_num

    @property
    def handler(self):
        """The module that handles this port (can be useful for
        emulator/testing).
        """
        return sys.modules[__name__]

    @property
    def value(self):
        """The value of the digital port."""
        return self.handler.read(self.port, self.board_num)

    @value.setter
    def value(self, data):
        return self.handler.write(data, self.port, self.board_num)


class DigitalInputPort(DigitalPort):
    """An digital input port on a PiFace product.

    .. note:: This hides the fact that inputs are active low.

       >>> input_port = pifacecommon.core.GPIOB
       >>> hex(pifacecommon.core.read(input_port))
       '0xFF'
       >>> hex(pifacecommon.core.DigitalInputPort(input_port).value)
       '0x00'
    """
    def __init__(self, port, board_num=0):
        super(DigitalInputPort, self).__init__(port, board_num)

    # redefine value property for input
    @property
    def value(self):
        """The value of the digital input port."""
        return 0xFF ^ self.handler.read(self.port, self.board_num)

    @value.setter
    def value(self, data):
        raise InputDeviceError("You cannot set an input's values!")


class DigitalOutputPort(DigitalPort):
    """An digital output port on a PiFace product"""
    def __init__(self, port, board_num=0):
        super(DigitalOutputPort, self).__init__(port, board_num)

    def all_on(self):
        """Turns all outputs on."""
        self.value = 0xFF

    def all_off(self):
        """Turns all outputs off."""
        self.value = 0

    def toggle(self):
        """Toggles all outputs."""
        self.value = 0xFF ^ self.value


class DigitalItem(DigitalPort):
    """A digital item connected to a pin on a PiFace product.
    Has most of the same properties of a Digital Port.
    """

    def __init__(self, pin_num, port, board_num=0):
        super(DigitalItem, self).__init__(port, board_num)
        self.pin_num = pin_num

    @property
    def value(self):
        """The value of the digital item."""
        return self.handler.read_bit(
            self.pin_num,
            self.port,
            self.board_num)

    @value.setter
    def value(self, data):
        return self.handler.write_bit(
            data,
            self.pin_num,
            self.port,
            self.board_num)


class DigitalInputItem(DigitalItem):
    """An digital input connected to a pin a PiFace product.

    .. note:: This hides the fact that inputs are active low.

       >>> input_port = pifacecommon.core.GPIOB
       >>> pifacecommon.core.read_bit(0, input_port)
       1
       >>> hex(pifacecommon.core.DigitalInputItem(0, input_port).value)
       0
    """
    def __init__(self, pin_num, port, board_num=0):
        super(DigitalInputItem, self).__init__(pin_num, port, board_num)

    # redefine value property for input
    @property
    def value(self):
        """The inverse value of the digital input item (inputs are active low).
        """
        return 1 ^ self.handler.read_bit(
            self.pin_num,
            self.port,
            self.board_num)

    @value.setter
    def value(self, data):
        raise InputDeviceError("You cannot set an input's values!")


class DigitalOutputItem(DigitalItem):
    """An output connected to a pin a PiFace Digital product."""
    def __init__(self, pin_num, port, board_num=0):
        super(DigitalOutputItem, self).__init__(pin_num, port, board_num)

    def turn_on(self):
        """Sets the digital output item's value to 1."""
        self.value = 1

    def turn_off(self):
        """Sets the digital output item's value to 0."""
        self.value = 0

    def toggle(self):
        """Toggles the digital output item's value."""
        self.value = not self.value


def init(bus=0, chip_select=0):
    """Initialises the SPI device file descriptor.

    :param bus: The SPI device bus number
    :type bus: int
    :param chip_select: The SPI device chip_select number
    :param chip_select: int
    :raises: InitError
    """
    spi_device = "%s%d.%d" % (SPIDEV, bus, chip_select)
    global spidev_fd
    try:
        spidev_fd = posix.open(spi_device, posix.O_RDWR)
    except OSError as e:
        raise InitError(
            "I can't see %s. Have you enabled the SPI module? (%s)"
            % (spi_device, SPI_HELP_LINK)
        )  # from e  # from is only available in Python 3


def deinit():
    """Closes the SPI device file descriptor."""
    global spidev_fd
    if spidev_fd:
        posix.close(spidev_fd)
    spidev_fd = None


def get_bit_mask(bit_num):
    """Translates a bit num to bit mask.

    :param bit_num: The bit number.
    :type bit_num: int
    :returns: int -- the bit mask
    :raises: RangeError

    >>> pifacecommon.core.get_bit_mask(0)
    1
    >>> pifacecommon.core.get_bit_mask(1)
    2
    >>> bin(pifacecommon.core.get_bit_mask(3))
    '0b1000'
    """
    if bit_num > 7 or bit_num < 0:
        raise RangeError(
            "Specified bit num (%d) out of range (0-7)." % bit_num)
    else:
        return 1 << (bit_num)


def get_bit_num(bit_pattern):
    """Returns the lowest bit num from a given bit pattern. Returns None if no
    bits set.

    :param bit_pattern: The bit pattern.
    :type bit_pattern: int
    :returns: int -- the bit number
    :returns: None -- no bits set

    >>> pifacecommon.core.get_bit_num(0)
    None
    >>> pifacecommon.core.get_bit_num(0b1)
    0
    >>> pifacecommon.core.get_bit_num(0b11000)
    3
    """
    if bit_pattern == 0:
        return None

    bit_num = 0  # assume bit 0
    while (bit_pattern & 1) == 0:
        bit_pattern = bit_pattern >> 1
        bit_num += 1
        if bit_num > 7:
            bit_num = 0
            break

    return bit_num


def read_bit(bit_num, address, board_num=0):
    """Returns the bit specified from the address.

    :param bit_num: The bit number to read from.
    :type bit_num: int
    :param address: The address to read from.
    :type address: int
    :param board_num: The board number to read from.
    :type board_num: int
    :returns: int -- the bit value from the address
    """
    value = read(address, board_num)
    bit_mask = get_bit_mask(bit_num)
    return 1 if value & bit_mask else 0


def write_bit(value, bit_num, address, board_num=0):
    """Writes the value given to the bit in the address specified.

    :param value: The value to write.
    :type value: int
    :param bit_num: The bit number to write to.
    :type bit_num: int
    :param address: The address to write to.
    :type address: int
    :param board_num: The board number to write to.
    :type board_num: int
    """
    bit_mask = get_bit_mask(bit_num)
    old_byte = read(address, board_num)
     # generate the new byte
    if value:
        new_byte = old_byte | bit_mask
    else:
        new_byte = old_byte & ~bit_mask
    write(new_byte, address, board_num)


def __get_device_opcode(board_num, read_write_cmd):
    """Returns the device opcode (as a byte).

    :param board_num: The board number to generate the opcode from.
    :type board_num: int
    :param read_write_cmd: Read or write command.
    :type read_write_cmd: int
    """
    board_addr_pattern = (board_num << 1) & 0xE  # 1 -> 0b0010, 3 -> 0b0110
    rw_cmd_pattern = read_write_cmd & 1  # make sure it's just 1 bit long
    return 0x40 | board_addr_pattern | rw_cmd_pattern


def read(address, board_num=0):
    """Returns the value of the address specified.

    :param address: The address to read from.
    :type address: int
    :param board_num: The board number to read from.
    :type board_num: int
    """
    return _pyver_read(address, board_num)


def _py3read(address, board_num):
    devopcode = __get_device_opcode(board_num, READ_CMD)
    op, addr, data = spisend(bytes((devopcode, address, 0)))
    return data


def _py2read(address, board_num):
    devopcode = __get_device_opcode(board_num, READ_CMD)
    op, addr, data = spisend(chr(devopcode)+chr(address)+chr(0))
    return ord(data)


def write(data, address, board_num=0):
    """Writes data to the address specified.

    :param data: The data to write.
    :type data: int
    :param address: The address to write to.
    :type address: int
    :param board_num: The board number to write to.
    :type board_num: int
    """
    _pyver_write(data, address, board_num)


def _py3write(data, address, board_num):
    devopcode = __get_device_opcode(board_num, WRITE_CMD)
    spisend(bytes((devopcode, address, data)))


def _py2write(data, address, board_num):
    devopcode = __get_device_opcode(board_num, WRITE_CMD)
    spisend(chr(devopcode)+chr(address)+chr(data))


# Python 2 support
PY3 = sys.version_info.major >= 3
_pyver_read = _py3read if PY3 else _py2read
_pyver_write = _py3write if PY3 else _py2write


def spisend(bytes_to_send):
    """Sends bytes via the SPI bus.

    :param bytes_to_send: The bytes to send on the SPI device.
    :type bytes_to_send: bytes
    :returns: bytes -- returned bytes from SPI device
    :raises: InitError
    """
    global spidev_fd
    if spidev_fd is None:
        raise InitError("Before spisend(), call init().")

    # make some buffer space to store reading/writing
    wbuffer = ctypes.create_string_buffer(bytes_to_send, len(bytes_to_send))
    rbuffer = ctypes.create_string_buffer(len(bytes_to_send))
    #rbuffer = ctypes.create_string_buffer(size=len(bytes_to_send)) should be

    # create the spi transfer struct
    transfer = spi_ioc_transfer(
        tx_buf=ctypes.addressof(wbuffer),
        rx_buf=ctypes.addressof(rbuffer),
        len=ctypes.sizeof(wbuffer)
    )

    # send the spi command
    ioctl(spidev_fd, SPI_IOC_MESSAGE(1), transfer)
    return ctypes.string_at(rbuffer, ctypes.sizeof(rbuffer))


def sleep_microseconds(microseconds):
    """Sleeps for the given number of microseconds.

    :param microseconds: Number of microseconds to sleep for.
    :type microseconds: int
    """
    # divide microseconds by 1 million for seconds
    seconds = microseconds / float(1000000)
    time.sleep(seconds)
