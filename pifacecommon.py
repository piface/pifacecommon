#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
import select
import time
from abc import ABCMeta
from fcntl import ioctl
from asm_generic_ioctl import _IOW

# spi stuff requires Python 3
assert sys.version_info.major >= 3, \
    __name__ + " is only supported on Python 3."


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

# interrupts
IN_EVENT_DIR_ON = 0
IN_EVENT_DIR_OFF = 1
IN_EVENT_DIR_BOTH = None

GPIO_INTERRUPT_PIN = 25
GPIO_INTERRUPT_DEVICE = "/sys/devices/virtual/gpio/gpio%d" % GPIO_INTERRUPT_PIN
GPIO_INTERRUPT_DEVICE_EDGE = '%s/edge' % GPIO_INTERRUPT_DEVICE
GPIO_INTERRUPT_DEVICE_VALUE = '%s/value' % GPIO_INTERRUPT_DEVICE
GPIO_EXPORT_FILE = "/sys/class/gpio/export"
GPIO_UNEXPORT_FILE = "/sys/class/gpio/unexport"

# max seconds to wait for file I/O (when enabling interrupts)
FILE_IO_TIMEOUT = 1

SPI_IOC_MAGIC = 107

SPIDEV = '/dev/spidev'

spidev_fd = None


class RangeError(Exception):
    pass


class InitError(Exception):
    pass


class InputDeviceError(Exception):
    pass


class DigitalPort(object):
    """A port on a PiFace Digital product"""
    __metaclass__ = ABCMeta

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
        return sys.modules[__name__]


class DigitalInputPort(DigitalPort):
    """An input port on a PiFace Digital product"""
    def __init__(self, port, board_num=0):
        super().__init__(port, board_num)

    @property
    def value(self):
        return 0xFF ^ self.handler.read(self.port, self.board_num)

    @value.setter
    def value(self, data):
        raise InputDeviceError("You cannot set an input's values!")


class DigitalOutputPort(DigitalPort):
    """An output port on a PiFace Digital product"""
    def __init__(self, port, board_num=0):
        super().__init__(port, board_num)

    @property
    def value(self):
        return self.handler.read(self.port, self.board_num)

    @value.setter
    def value(self, data):
        return self.handler.write(data, self.port, self.board_num)

    def all_on(self):
        self.value = 0xFF

    def all_off(self):
        self.value = 0

    def toggle(self):
        self.value = 0xFF ^ self.value


class DigitalItem(DigitalPort):
    """An item connected to a pin on a PiFace Digital product.
    Has most of the same properties of a Digital Port.
    """
    __metaclass__ = ABCMeta

    def __init__(self, pin_num, port, board_num=0):
        super().__init__(port, board_num)
        self.pin_num = pin_num


class DigitalInputItem(DigitalItem):
    """An input connected to a pin a PiFace Digital product"""
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
    """An output connected to a pin a PiFace Digital product"""
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


class InputFunctionMap(list):
    """Maps inputs pins to functions.

    Use the register method to map inputs to functions.

    Each function is passed the interrupt bit map as a byte and the input
    port as a byte. The return value of the function specifies whether the
    wait_for_input loop should continue (True is continue).

    Register Parameters (*optional):
    input_num  - input pin number
    direction  - direction of change
                     IN_EVENT_DIR_ON
                     IN_EVENT_DIR_OFF
                     IN_EVENT_DIR_BOTH
    callback   - function to run when interrupt is detected
    board_num* - what PiFace digital board to check

    Example:
    def my_callback(interrupt_flag_bit, input_byte):
         # if interrupt_flag_bit = 0b00001000: pin 3 caused the interrupt
         # if input_byte = 0b10110111: pins 6 and 3 activated
        print(bin(interrupted_bit), bin(input_byte))
        return True  # keep waiting for interrupts
    """
    def register(self, input_num, direction, callback, board_num=0):
        self.append({
            'input_num': input_num,
            'direction': direction,
            'callback': callback,
            'board_num': board_num,
        })


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
    try:
        spidev_fd = posix.open(
            "%s%d.%d" % (SPIDEV, bus, chip_select),
            posix.O_RDWR
        )
    except OSError as e:
        raise InitError(e)


def deinit():
    """Closes the spidev file descriptor"""
    global spidev_fd
    if spidev_fd:
        posix.close(spidev_fd)
    spidev_fd = None


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


def sleep_microseconds(microseconds):
    # divide microseconds by 1 million for seconds
    seconds = microseconds / float(1000000)
    time.sleep(seconds)


# interrupts
def wait_for_interrupt(port, input_func_map=None, timeout=None):
    """Waits for an port event (change)

    Paramaters:
    port           - What port are we waiting for interrupts on? GPIOA or B?
    input_func_map - An InputFunctionMap object describing callbacks
    timeout        - How long we should wait before giving up and exiting the
                     function
    """
    enable_interrupts(port)

    # set up epoll (can't do it in enable_interrupts for some reason)
    gpio25 = open(GPIO_INTERRUPT_DEVICE_VALUE, 'r')
    epoll = select.epoll()
    epoll.register(gpio25, select.EPOLLIN | select.EPOLLET)

    while True:
        # wait here until input
        try:
            events = _wait_for_event(epoll, timeout)
        except KeyboardInterrupt:
            break

        # if we have some events...
        if len(events) <= 0:
            break

        # ...and a map
        if input_func_map:
            keep_waiting = _call_mapped_input_functions(port, input_func_map)
            if not keep_waiting:
                break
        else:
            break  # there is no ifm

    epoll.close()
    disable_interrupts(port)


def _wait_for_event(epoll, timeout=None):
    """Waits for an event on the epoll, returns a list of events
    This will hang, may throw KeyboardInterrupt
    """
    return epoll.poll(timeout) if timeout else epoll.poll()


def _call_mapped_input_functions(port, input_func_map):
    """Finds which board caused the interrupt and calls the mapped
    function.
    Returns whether the wait_for_input function should keep waiting for input
    """
    if port == GPIOA:
        intflag = INTFA 
        intcapture = INTCAPA
    else:
        intflag = INTFB
        intcapture = INTCAPB

    for board_i in range(MAX_BOARDS):
        this_board_ifm = [m for m in input_func_map if m['board_num'] == board_i]

        # read the interrupt status of this PiFace board
        # interrupt bit (int_bit) - bit map showing what caused the interrupt
        int_flag_bit = read(intflag, board_i)

        if int_flag_bit == 0:
            continue  # The interrupt has not been flagged on this board
        int_bit_num = get_bit_num(int_flag_bit)
        
        # interrupt byte (int_byte) - snapshot of in port when int occured
        int_byte = read(intcapture, board_i)

        # direction - whether the bit changed into a 1 or a 0
        direction = (int_flag_bit & int_byte) >> int_bit_num

        # for each mapping (on this board) see if we have a callback
        for mapping in this_board_ifm:
            if int_bit_num == mapping['input_num'] and \
                    (mapping['direction'] is None or
                        direction == mapping['direction']):
                # run the callback
                keep_waiting = mapping['callback'](int_flag_bit, int_byte)

                # stop waiting for interrupts, by default
                if keep_waiting is None:
                    keep_waiting = False

                return keep_waiting

    # This event does not have a mapped function, keep waiting
    return True


# tp - don't know if this is needed.
def clear_interrupts(port):
    """Clears the interrupt flags by 'read'ing the capture register
    on all boards
    """
    intcap = INTCAPA if port == GPIOA else INTCAPB
    for i in range(MAX_BOARDS):
        read(intcap, i)


def enable_interrupts(port):
    # enable interrupts
    int_enable_port = GPINTENA if port == GPIOA else GPINTENB
    for board_index in range(MAX_BOARDS):
        write(0xff, int_enable_port, board_index)

    try:
        _bring_gpio_interrupt_into_userspace()
        _set_gpio_interrupt_edge()
    except Timeout as e:
        raise InterruptEnableException(
            "There was an error bringing gpio%d into userspace. %s" % \
            (GPIO_INTERRUPT_PIN, e.message)
        )


def _bring_gpio_interrupt_into_userspace():
    try:
        # is it already there?
        with open(GPIO_INTERRUPT_DEVICE_VALUE): return
    except IOError:
        # no, bring it into userspace
        with open(GPIO_EXPORT_FILE, 'w') as export_file:
            export_file.write(str(GPIO_INTERRUPT_PIN))

        _wait_until_file_exists(GPIO_INTERRUPT_DEVICE_VALUE)


def _set_gpio_interrupt_edge():
    # we're only interested in the falling edge (1 -> 0)
    start_time = time.time()
    time_limit = start_time + FILE_IO_TIMEOUT
    while time.time() < time_limit:
        try:
            with open(GPIO_INTERRUPT_DEVICE_EDGE, 'w') as gpio_edge:
                gpio_edge.write('falling')
                return
        except IOError:
            pass


def _wait_until_file_exists(filename):
    start_time = time.time()
    time_limit = start_time + FILE_IO_TIMEOUT
    while time.time() < time_limit:
        try:
            with open(filename): return
        except IOError:
            pass
    
    raise Timeout("Waiting too long for %s." % filename)


def disable_interrupts(port):
    # neither edge
    with open(GPIO_INTERRUPT_DEVICE_EDGE, 'w') as gpio25edge:
        gpio25edge.write('none')

    # remove the pin from userspace
    with open(GPIO_UNEXPORT_FILE, 'w') as unexport_file:
        unexport_file.write(str(GPIO_INTERRUPT_PIN))

    # disable the interrupt
    int_enable_port = GPINTENA if port == GPIOA else GPINTENB
    for board_index in range(MAX_BOARDS):
        write(0, int_enable_port, board_index)
