#######
Example
#######
Here are some examples of how to use pifacecommon::

    $ python3
    >>> import pifacecommon
    >>> pifacecommon.init()
    >>> pifacecommon.write(0xAA, pifacecommon.GPIOA)
    >>> pifacecommon.read(pifacecommon.GPIOA)
    0xAA
    >>> pifacecommon.write_bit(1, 0, pifacecommon.GPIOA)
    >>> pifacecommon.read_bit(0, pifacecommon.GPIOA)
    1
