def get_bit_mask(bit_num):
    """Returns as bit mask with bit_num set.

    :param bit_num: The bit number.
    :type bit_num: int
    :returns: int -- the bit mask
    :raises: RangeError

    >>> bin(pifacecommon.core.get_bit_mask(0))
    1
    >>> pifacecommon.core.get_bit_mask(1)
    2
    >>> bin(pifacecommon.core.get_bit_mask(3))
    '0b1000'
    """
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


def sleep_microseconds(microseconds):
    """Sleeps for the given number of microseconds.

    :param microseconds: Number of microseconds to sleep for.
    :type microseconds: int
    """
    # divide microseconds by 1 million for seconds
    seconds = microseconds / float(1000000)
    time.sleep(seconds)
