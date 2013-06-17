#!/usr/bin/env python3
"""Provides interrupt logic for interfacing with PiFace Products
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
import select
import time
from .core import (
    MAX_BOARDS,
    GPIOA,
    GPIOB,
    GPINTENA,
    GPINTENB,
    INTFA,
    INTFB,
    INTCAPA,
    INTCAPB,
    get_bit_num,
    read,
    write,
)


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

    kb_interrupt = None

    while True:
        # wait here until input
        try:
            events = _wait_for_event(epoll, timeout)
        except KeyboardInterrupt as k:
            kb_interrupt = k
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

    # deal with the kb_interrupt here
    if kb_interrupt is not None:
        raise kb_interrupt


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
        this_board_ifm = \
            [m for m in input_func_map if m['board_num'] == board_i]

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
            "There was an error bringing gpio%d into userspace. %s" %
            (GPIO_INTERRUPT_PIN, e.message)
        )


def _bring_gpio_interrupt_into_userspace():
    try:
        # is it already there?
        with open(GPIO_INTERRUPT_DEVICE_VALUE):
            return
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
            with open(filename):
                return
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
