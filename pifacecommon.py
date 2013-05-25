#!/usr/bin/env python3
"""Provides common I/O methods for interfacing with PiFace Products
Copyright (C) 2013 Thomas Preston <thomasmarkpreston@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import sys
import ctypes
import posix
from fcntl import ioctl
from asm_generic_ioctl import _IOW

# spi stuff requires Python 3
assert sys.version_info.major >= 3, \
    __name__ + " is only supported on Python 3."


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
SEQOP_ON = 0x20
DISSLW_ON = 0x10  # slew rate
DISSLW_OFF = 0x00
HAEN_ON = 0x08  # hardware addressing
HAEN_OFF = 0x00
ODR_ON = 0x04  # open drain for interupts
ODR_OFF = 0x00
INTPOL_HIGH = 0x02  # interupt polarity
INTPOL_LOW = 0x00

SPI_IOC_MAGIC = 107

SPIDEV = '/dev/spidev'

spidev_fd = None


class RangeError(Exception):
    pass


class InitError(Exception):
    pass


class InputDeviceError(Exception):
    pass


class DigitalItem(object):
    """An item connected to a pin on a PiFace product"""
    def __init__(self, pin_num, port, board_num=0):
        self.pin_num = pin_num
        self.port = port
        if board_num < 0 or board_num >= MAX_BOARDS:
            raise RangeError(
                "Specified board index (%d) out of range." % board_num
            )
        else:
            self.board_num = board_num

    @property
    def handler(self):
        return sys.modules[__name__]


class DigitalInputItem(DigitalItem):
    """An input connected to a pin a PiFace product"""
    def __init__(self, pin_num, port, board_num=0):
        super().__init__(pin_num, port, board_num)

    @property
    def value(self):
        return 1 ^ self.handler.read_bit(
            self.pin_num,
            self.port,
            self.board_num)

    @value.setter
    def value(self, data):
        raise InputDeviceError("You cannot set an input's values!")


class DigitalOutputItem(DigitalItem):
    """An output connected to a pin a PiFace product"""
    def __init__(self, pin_num, port, board_num=0):
        super().__init__(pin_num, port, board_num)

    @property
    def value(self):
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

    def turn_on(self):
        self.value = 1

    def turn_off(self):
        self.value = 0

    def toggle(self):
        self.value = not self.value


class _spi_ioc_transfer(ctypes.Structure):
    """SPI ioc transfer structure (from linux/spi/spidev.h)"""
    _fields_ = [
        ("tx_buf", ctypes.c_uint64),
        ("rx_buf", ctypes.c_uint64),
        ("len", ctypes.c_uint32),
        ("speed_hz", ctypes.c_uint32),
        ("delay_usecs", ctypes.c_uint16),
        ("bits_per_word", ctypes.c_uint8),
        ("cs_change", ctypes.c_uint8),
        ("pad", ctypes.c_uint32)]


def init(bus=0, chip_select=0):
    """Initialises the PiFace Digital board"""
    global spidev_fd
    spidev_fd = posix.open(
        "%s%d.%d" % (SPIDEV, bus, chip_select),
        posix.O_RDWR
    )


def deinit():
    """Closes the spidev file descriptor"""
    global spidev_fd
    posix.close(spidev_fd)


def get_bit_mask(bit_num):
    """Translates a pin num to pin bit mask. First pin is pin0."""
    if bit_num > 7 or bit_num < 0:
        raise RangeError(
            "Specified bit num (%d) out of range (0-7)." % bit_num)
    else:
        return 1 << (bit_num)


def get_bit_num(bit_pattern):
    """Returns the lowest pin num from a given bit pattern"""
    bit_num = 0  # assume bit 0
    while (bit_pattern & 1) == 0:
        bit_pattern = bit_pattern >> 1
        bit_num += 1
        if bit_num > 7:
            bit_num = 0
            break

    return bit_num


def read_bit(bit_num, address, board_num=0):
    """Returns the bit specified from the address"""
    value = read(address, board_num)
    bit_mask = get_bit_mask(bit_num)
    return 1 if value & bit_mask else 0


def write_bit(value, bit_num, address, board_num=0):
    """Writes the value given to the bit specified"""
    bit_mask = get_bit_mask(bit_num)
    old_byte = read(address, board_num)
     # generate the new byte
    if value:
        new_byte = old_byte | bit_mask
    else:
        new_byte = old_byte & ~bit_mask
    write(new_byte, address, board_num)


def __get_device_opcode(board_num, read_write_cmd):
    """Returns the device opcode (as a byte)"""
    board_addr_pattern = (board_num << 1) & 0xE  # 1 -> 0b0010, 3 -> 0b0110
    rw_cmd_pattern = read_write_cmd & 1  # make sure it's just 1 bit long
    return 0x40 | board_addr_pattern | rw_cmd_pattern


def read(address, board_num=0):
    """Reads from the address specified"""
    devopcode = __get_device_opcode(board_num, READ_CMD)
    op, addr, data = spisend((devopcode, address, 0))  # data byte is not used
    return data


def write(data, address, board_num=0):
    """Writes data to the address specified"""
    devopcode = __get_device_opcode(board_num, WRITE_CMD)
    op, addr, data = spisend((devopcode, address, data))


def spisend(bytes_to_send):
    """Sends bytes via the SPI bus"""
    global spidev_fd
    if spidev_fd is None:
        raise InitError("Before spisend(), call init().")

     # make some buffer space to store reading/writing
    write_bytes = bytes(bytes_to_send)
    wbuffer = ctypes.create_string_buffer(write_bytes, len(write_bytes))
    rbuffer = ctypes.create_string_buffer(len(bytes_to_send))

     # create the spi transfer struct
    transfer = _spi_ioc_transfer(
        tx_buf=ctypes.addressof(wbuffer),
        rx_buf=ctypes.addressof(rbuffer),
        len=ctypes.sizeof(wbuffer))

     # send the spi command (with a little help from asm-generic
    iomsg = _IOW(SPI_IOC_MAGIC, 0, ctypes.c_char*ctypes.sizeof(transfer))
    ioctl(spidev_fd, iomsg, ctypes.addressof(transfer))
    return ctypes.string_at(rbuffer, ctypes.sizeof(rbuffer))
