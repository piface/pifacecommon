pifacecommon
============

Common functions for interacting with PiFace products. Also available from 
[PyPI](https://pypi.python.org/pypi/pifacecommon/)

Auto Installation
=================
### GitHub

    $ git clone https://github.com/piface/pifacecommon.git
    $ cd pifacecommon
    $ sudo ./install.sh

### PyPI
(You will have to set up SPI stuff manually if this is your first time)

    $ sudo easy_install3 pifacecommon

Examples
========

    $ python3
    >>> import pifacecommon
    >>> pifacecommon.init()
    >>> pifacecommon.write(0xAA, pifacecommon.GPIOA)
    >>> pifacecommon.read(pifacecommon.GPIOA)
    0xAA
