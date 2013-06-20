#######
Example
#######
Here is some example usage of pifacecommon::

    $ python3
    >>> import pifacecommon
    >>> pifacecommon.init()
    >>> pifacecommon.write(0xAA, pifacecommon.GPIOA)
    >>> pifacecommon.read(pifacecommon.GPIOA)
    0xAA
