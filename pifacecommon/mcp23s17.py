import os
import sys
from .core import (
    get_bit_mask,
    get_bit_num,
)
from .spi import SPIDevice
import pifacecommon.interrupts


# Python 2 support
PY3 = sys.version_info[0] >= 3

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
OLATA = 0x14  # output latch A
OLATB = 0x15  # output latch B

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

LOWER_NIBBLE, UPPER_NIBBLE = range(2)


class MCP23S17(SPIDevice):
    """Microchip's MCP23S17: A 16-Bit I/O Expander with Serial Interface.

    :attribute: iodira/iodirb -- Controls the direction of the data I/O.
    :attribute: ipola/ipolb --This register allows the user to configure
                              the polarity on the corresponding GPIO port
                              bits.
    :attribute: gpintena/gpintenb -- The GPINTEN register controls the
                                     interrupt-onchange feature for each
                                     pin.
    :attribute: defvala/defvalb --The default comparison value is
                                  configured in the DEFVAL register.
    :attribute: intcona/intconb --The INTCON register controls how the
                                  associated pin value is compared for
                                  the interrupt-on-change feature.
    :attribute: iocon --The IOCON register contains several bits for
                        configuring the device.
    :attribute: gppua/gppub --The GPPU register controls the pull-up
                              resistors for the port pins.
    :attribute: intfa/intfb --The INTF register reflects the interrupt
                              condition on the port pins of any pin that
                              is enabled for interrupts via the GPINTEN
                              register.
    :attribute: intcapa/intcapb -- The INTCAP register captures the GPIO
                                   port value at the time the interrupt
                                   occurred.
    :attribute: gpioa/gpiob -- The GPIO register reflects the value on
                               the port.
    :attribute: olata/olatb -- The OLAT register provides access to the
                               output latches.
    """
    def __init__(self, hardware_addr=0, bus=0, chip_select=0, speed_hz=100000):
        super(MCP23S17, self).__init__(bus, chip_select, speed_hz=speed_hz)
        self.hardware_addr = hardware_addr

        self.iodira = MCP23S17Register(IODIRA, self)
        self.iodirb = MCP23S17Register(IODIRB, self)
        self.ipola = MCP23S17Register(IPOLA, self)
        self.ipolb = MCP23S17Register(IPOLB, self)
        self.gpintena = MCP23S17Register(GPINTENA, self)
        self.gpintenb = MCP23S17Register(GPINTENB, self)
        self.defvala = MCP23S17Register(DEFVALA, self)
        self.defvalb = MCP23S17Register(DEFVALB, self)
        self.intcona = MCP23S17Register(INTCONA, self)
        self.intconb = MCP23S17Register(INTCONB, self)
        self.iocon = MCP23S17Register(IOCON, self)
        self.gppua = MCP23S17Register(GPPUA, self)
        self.gppub = MCP23S17Register(GPPUB, self)
        self.intfa = MCP23S17Register(INTFA, self)
        self.intfb = MCP23S17Register(INTFB, self)
        self.intcapa = MCP23S17Register(INTCAPA, self)
        self.intcapb = MCP23S17Register(INTCAPB, self)
        self.gpioa = MCP23S17Register(GPIOA, self)
        self.gpiob = MCP23S17Register(GPIOB, self)
        self.olata = MCP23S17Register(OLATA, self)
        self.olatb = MCP23S17Register(OLATB, self)

    def _get_spi_control_byte(self, read_write_cmd):
        """Returns an SPI control byte.

        The MCP23S17 is a slave SPI device. The slave address contains
        four fixed bits and three user-defined hardware address bits
        (if enabled via IOCON.HAEN) (pins A2, A1 and A0) with the
        read/write bit filling out the control byte::

            +--------------------+
            |0|1|0|0|A2|A1|A0|R/W|
            +--------------------+
             7 6 5 4 3  2  1   0

        :param read_write_cmd: Read or write command.
        :type read_write_cmd: int
        """
        # board_addr_pattern = (self.hardware_addr & 0b111) << 1
        board_addr_pattern = (self.hardware_addr << 1) & 0xE
        rw_cmd_pattern = read_write_cmd & 1  # make sure it's just 1 bit long
        return 0x40 | board_addr_pattern | rw_cmd_pattern

    def read(self, address):
        """Returns the value of the address specified.

        :param address: The address to read from.
        :type address: int
        """
        return self._pyver_read(address)

    def _py3read(self, address):
        ctrl_byte = self._get_spi_control_byte(READ_CMD)
        op, addr, data = self.spisend(bytes((ctrl_byte, address, 0)))
        return data

    def _py2read(self, address):
        ctrl_byte = self._get_spi_control_byte(READ_CMD)
        op, addr, data = self.spisend(chr(ctrl_byte)+chr(address)+chr(0))
        return ord(data)

    def write(self, data, address):
        """Writes data to the address specified.

        :param data: The data to write.
        :type data: int
        :param address: The address to write to.
        :type address: int
        """
        self._pyver_write(data, address)

    def _py3write(self, data, address):
        ctrl_byte = self._get_spi_control_byte(WRITE_CMD)
        self.spisend(bytes((ctrl_byte, address, data)))

    def _py2write(self, data, address):
        ctrl_byte = self._get_spi_control_byte(WRITE_CMD)
        self.spisend(chr(ctrl_byte)+chr(address)+chr(data))

    # Python 2 support
    _pyver_read = _py3read if PY3 else _py2read
    _pyver_write = _py3write if PY3 else _py2write

    def read_bit(self, bit_num, address):
        """Returns the bit specified from the address.

        :param bit_num: The bit number to read from.
        :type bit_num: int
        :param address: The address to read from.
        :type address: int
        :returns: int -- the bit value from the address
        """
        value = self.read(address)
        bit_mask = get_bit_mask(bit_num)
        return 1 if value & bit_mask else 0

    def write_bit(self, value, bit_num, address):
        """Writes the value given to the bit in the address specified.

        :param value: The value to write.
        :type value: int
        :param bit_num: The bit number to write to.
        :type bit_num: int
        :param address: The address to write to.
        :type address: int
        """
        bit_mask = get_bit_mask(bit_num)
        old_byte = self.read(address)
         # generate the new byte
        if value:
            new_byte = old_byte | bit_mask
        else:
            new_byte = old_byte & ~bit_mask
        self.write(new_byte, address)

    def clear_interrupts(self, port):
        """Clears the interrupt flags by 'read'ing the capture register."""
        self.read(INTCAPA if port == GPIOA else INTCAPB)


class MCP23S17RegisterBase(object):
    """Base class for objects on an 8-bit register inside an MCP23S17."""
    def __init__(self, address, chip):
        self.address = address
        self.chip = chip


class MCP23S17Register(MCP23S17RegisterBase):
    """An 8-bit register inside an MCP23S17."""
    def __init__(self, address, chip):
        super(MCP23S17Register, self).__init__(address, chip)
        self.lower_nibble = MCP23S17RegisterNibble(LOWER_NIBBLE, self.address,
                                                   self.chip)
        self.upper_nibble = MCP23S17RegisterNibble(UPPER_NIBBLE, self.address,
                                                   self.chip)
        self.bits = [MCP23S17RegisterBit(i, self.address, self.chip)
                     for i in range(8)]

    @property
    def value(self):
        return self.chip.read(self.address)

    @value.setter
    def value(self, v):
        self.chip.write(v, self.address)

    def all_high(self):
        self.value = 0xFF

    def all_low(self):
        self.value = 0x00

    all_on = all_high
    all_off = all_low

    def toggle(self):
        self.value = 0xFF ^ self.value


class MCP23S17RegisterNeg(MCP23S17Register):
    """An negated 8-bit register inside an MCP23S17."""
    def __init__(self, address, chip):
        super(MCP23S17RegisterNeg, self).__init__(address, chip)
        self.lower_nibble = MCP23S17RegisterNibbleNeg(LOWER_NIBBLE,
                                                      self.address,
                                                      self.chip)
        self.upper_nibble = MCP23S17RegisterNibbleNeg(UPPER_NIBBLE,
                                                      self.address,
                                                      self.chip)
        self.bits = [MCP23S17RegisterBitNeg(i, self.address, self.chip)
                     for i in range(8)]

    @property
    def value(self):
        return 0xFF ^ self.chip.read(self.address)

    @value.setter
    def value(self, v):
        self.chip.write(0xFF ^ v, self.address)


class MCP23S17RegisterNibble(MCP23S17RegisterBase):
    """An 4-bit nibble inside a register inside an MCP23S17."""
    def __init__(self, nibble, address, chip):
        super(MCP23S17RegisterNibble, self).__init__(address, chip)
        self.nibble = nibble
        range_start = 0 if self.nibble == LOWER_NIBBLE else 4
        range_end = 4 if self.nibble == LOWER_NIBBLE else 8
        self.bits = [MCP23S17RegisterBit(i, self.address, self.chip)
                     for i in range(range_start, range_end)]

    @property
    def value(self):
        if self.nibble == LOWER_NIBBLE:
            return self.chip.read(self.address) & 0xF
        elif self.nibble == UPPER_NIBBLE:
            return (self.chip.read(self.address) & 0xF0) >> 4

    @value.setter
    def value(self, v):
        register_value = self.chip.read(self.address)
        if self.nibble == LOWER_NIBBLE:
            register_value &= 0xF0  # clear
            register_value ^= (v & 0x0F)  # set
        elif self.nibble == UPPER_NIBBLE:
            register_value &= 0x0F  # clear
            register_value ^= ((v << 4) & 0xF0)  # set
        self.chip.write(register_value, self.address)

    def all_high(self):
        self.value = 0xF

    def all_low(self):
        self.value = 0x0

    all_on = all_high
    all_off = all_low

    def toggle(self):
        self.value = 0xF ^ self.value


class MCP23S17RegisterNibbleNeg(MCP23S17RegisterNibble):
    """A negated 4-bit nibble inside a register inside an MCP23S17."""
    def __init__(self, nibble, address, chip):
        super(MCP23S17RegisterNibbleNeg, self).__init__(nibble, address, chip)
        self.nibble = nibble
        range_start = 0 if self.nibble == LOWER_NIBBLE else 4
        range_end = 4 if self.nibble == LOWER_NIBBLE else 8
        self.bits = [MCP23S17RegisterBitNeg(i, self.address, self.chip)
                     for i in range(range_start, range_end)]

    @property
    def value(self):
        if self.nibble == LOWER_NIBBLE:
            v = self.chip.read(self.address) & 0xF
        elif self.nibble == UPPER_NIBBLE:
            v = (self.chip.read(self.address) & 0xF0) >> 4
        return 0xF ^ v

    @value.setter
    def value(self, v):
        register_value = self.chip.read(self.address)
        if self.nibble == LOWER_NIBBLE:
            register_value &= 0xF0  # clear
            register_value ^= (v & 0x0F ^ 0x0F)  # set
        elif self.nibble == UPPER_NIBBLE:
            register_value &= 0x0F  # clear
            register_value ^= ((v << 4) & 0xF0 ^ 0xF0)  # set
        self.chip.write(register_value, self.address)


class MCP23S17RegisterBit(MCP23S17RegisterBase):
    """A bit inside register inside an MCP23S17."""
    def __init__(self, bit_num, address, chip):
        super(MCP23S17RegisterBit, self).__init__(address, chip)
        self.bit_num = bit_num

    @property
    def value(self):
        return self.chip.read_bit(self.bit_num, self.address)

    @value.setter
    def value(self, v):
        self.chip.write_bit(v, self.bit_num, self.address)

    def set_high(self):
        self.value = 1

    def set_low(self):
        self.value = 0

    turn_on = set_high
    turn_off = set_low

    def toggle(self):
        self.value = 1 ^ self.value


class MCP23S17RegisterBitNeg(MCP23S17RegisterBit):
    """A negated bit inside register inside an MCP23S17."""
    def __init__(self, bit_num, address, chip):
        super(MCP23S17RegisterBitNeg, self).__init__(bit_num, address, chip)

    @property
    def value(self):
        return 1 ^ self.chip.read_bit(self.bit_num, self.address)

    @value.setter
    def value(self, v):
        self.chip.write_bit(v ^ 1, self.bit_num, self.address)
