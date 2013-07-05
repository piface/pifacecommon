# -*- coding: utf-8 -*-
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

# constants
from .core import (
    MAX_BOARDS,
    IODIRA,
    IODIRB,
    IPOLA,
    IPOLB,
    GPINTENA,
    GPINTENB,
    DEFVALA,
    DEFVALB,
    INTCONA,
    INTCONB,
    IOCON,
    GPPUA,
    GPPUB,
    INTFA,
    INTFB,
    INTCAPA,
    INTCAPB,
    GPIOA,
    GPIOB,
    BANK_OFF,
    BANK_ON,
    INT_MIRROR_ON,
    INT_MIRROR_OFF,
    SEQOP_OFF,
    SEQOP_ON,
    DISSLW_ON,
    DISSLW_OFF,
    HAEN_ON,
    HAEN_OFF,
    ODR_ON,
    ODR_OFF,
    INTPOL_HIGH,
    INTPOL_LOW,
)

from .interrupts import (
    IN_EVENT_DIR_ON,
    IN_EVENT_DIR_OFF,
    IN_EVENT_DIR_BOTH,
)

# classes
from .core import (
    DigitalPort,
    DigitalInputPort,
    DigitalOutputPort,
    DigitalItem,
    DigitalInputItem,
    DigitalOutputItem,
)

from .interrupts import (
    InputFunctionMap,
)

# functions
from .core import (
    init,
    deinit,
    get_bit_mask,
    get_bit_num,
    read_bit,
    write_bit,
    read,
    write,
    spisend,
    sleep_microseconds,
)

from .interrupts import (
    wait_for_interrupt,
    clear_interrupts,
    enable_interrupts,
    disable_interrupts,
)
