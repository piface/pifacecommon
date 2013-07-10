#######
Example
#######
Here are some examples of how to use pifacecommon::

    $ python3
    >>> import pifacecommon
    >>> pifacecommon.core.init()
    >>> pifacecommon.core.write(0xAA, pifacecommon.core.GPIOA)
    >>> pifacecommon.core.read(pifacecommon.core.GPIOA)
    0xAA
    >>> pifacecommon.core.write_bit(1, 0, pifacecommon.core.GPIOA)
    >>> pifacecommon.core.read_bit(0, pifacecommon.core.GPIOA)
    1
