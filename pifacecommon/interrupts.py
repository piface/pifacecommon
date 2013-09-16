import threading
import multiprocessing
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
IODIR_ON = 0
IODIR_OFF = 1
IODIR_BOTH = None
# IN_EVENT_DIR_OFF = INPUT_DIRECTION_OFF = 1
# IN_EVENT_DIR_BOTH = INPUT_DIRECTION_BOTH = None

GPIO_INTERRUPT_PIN = 25
GPIO_INTERRUPT_DEVICE = "/sys/devices/virtual/gpio/gpio%d" % GPIO_INTERRUPT_PIN
GPIO_INTERRUPT_DEVICE_EDGE = '%s/edge' % GPIO_INTERRUPT_DEVICE
GPIO_INTERRUPT_DEVICE_VALUE = '%s/value' % GPIO_INTERRUPT_DEVICE
GPIO_EXPORT_FILE = "/sys/class/gpio/export"
GPIO_UNEXPORT_FILE = "/sys/class/gpio/unexport"

# max seconds to wait for file I/O (when enabling interrupts)
FILE_IO_TIMEOUT = 1

READY_FOR_EVENTS = "ready for events"

# deboucing
DEFAULT_SETTLE_TIME = 0.020  # 20ms


class Timeout(Exception):
    pass


class InterruptEvent(object):
    """An interrupt event."""
    def __init__(
            self, interrupt_flag, interrupt_capture, board_num, timestamp):
        self.interrupt_flag = interrupt_flag
        self.interrupt_capture = interrupt_capture
        self.board_num = board_num
        self.timestamp = timestamp

    @property
    def pin_num(self):
        return get_bit_num(self.interrupt_flag)

    @property
    def direction(self):
        return (self.interrupt_flag & self.interrupt_capture) >> self.pin_num


class FunctionMap(object):
    """Maps something to a callback function.
    (This is an abstract class, you must implement a SomethingFunctionMap).
    """
    def __init__(self, callback, settle_time=None):
        self.callback = callback
        self.settle_time = settle_time


class PinFunctionMap(FunctionMap):
    """Maps an IO pin and a direction to callback function."""
    def __init__(self, pin_num, direction, callback, settle_time):
        self.pin_num = pin_num
        self.direction = direction
        super(PinFunctionMap, self).__init__(callback, settle_time)


class EventQueue(object):
    """Stores events in a queue."""
    def __init__(self, pin_function_maps):
        super(EventQueue, self).__init__()
        self.last_event_time = [0]*8  # last event time on each pin
        self.pin_function_maps = pin_function_maps
        self.queue = multiprocessing.Queue()

    def add_event(self, event):
        """Adds events to the queue. Will ignore events that occur before the
        settle time for that pin/direction. Such events are assumed to be
        bouncing.
        """
        # find out the pin settle time
        for pin_function_map in self.pin_function_maps:
            if pin_function_map.pin_num == event.pin_num and \
                    pin_function_map.direction == event.direction:
                pin_settle_time = pin_function_map.settle_time
                break
        else:
            # Couldn't find event in map, don't bother adding it to the queue
            return

        threshold_time = self.last_event_time[event.pin_num] + pin_settle_time
        if event.timestamp > threshold_time:
            self.put(event)
            self.last_event_time[event.pin_num] = event.timestamp

    def put(self, thing):
        self.queue.put(thing)

    def get(self):
        return self.queue.get()


class PortEventListener(object):
    """Listens for port events and calls the registered functions.

    >>> def print_flag(event):
    ...     print(event.interrupt_flag)
    ...
    >>> port = pifacecommon.core.GPIOA
    >>> listener = pifacecommon.interrupts.PortEventListener(port)
    >>> listener.register(0, pifacecommon.interrupts.IODIR_ON, print_flag)
    >>> listener.activate()
    """

    TERMINATE_SIGNAL = "astalavista"

    def __init__(self, port, board_num=0):
        self.port = port
        self.board_num = board_num
        self.pin_function_maps = list()
        self.event_queue = EventQueue(self.pin_function_maps)
        self.detector = multiprocessing.Process(
            target=watch_port_events,
            args=(
                self.port,
                self.board_num,
                self.pin_function_maps,
                self.event_queue))
        self.dispatcher = threading.Thread(
            target=handle_events,
            args=(
                self.pin_function_maps,
                self.event_queue,
                _event_matches_pin_function_map,
                PortEventListener.TERMINATE_SIGNAL))

    def register(self, pin_num, direction, callback,
                 settle_time=DEFAULT_SETTLE_TIME):
        """Registers a pin number and direction to a callback function.

        :param pin_num: The pin pin number.
        :type pin_num: int
        :param direction: The event direction
            (use: IODIR_ON/IODIR_OFF/IODIR_BOTH)
        :type direction: int
        :param callback: The function to run when event is detected.
        :type callback: function
        :param settle_time: Time within which subsequent events are ignored.
        :type settle_time: int
        """
        self.pin_function_maps.append(
            PinFunctionMap(pin_num, direction, callback, settle_time))

    def activate(self):
        """When activated the :class:`PortEventListener` will run callbacks
        associated with pins/directions.
        """
        self.detector.start()
        self.dispatcher.start()

    def deactivate(self):
        """When deactivated the :class:`PortEventListener` will not run
        anything.
        """
        self.event_queue.put(self.TERMINATE_SIGNAL)
        self.dispatcher.join()
        self.detector.terminate()


def _event_matches_pin_function_map(event, pin_function_map):
    pin_match = event.pin_num == pin_function_map.pin_num
    direction_match = pin_function_map.direction is None
    direction_match |= event.direction == pin_function_map.direction
    return pin_match and direction_match


def watch_port_events(port, board_num, pin_function_maps, event_queue):
    """Waits for a port event. When a port event occurs it is placed onto the
    event queue.

    :param port: The port we are waiting for interrupts on (GPIOA/GPIOB).
    :type port: int
    :param board_num: The board we are waiting for interrupts on.
    :type board_num: int
    :param pin_function_maps: A list of classes that have inheritted from
        :class:`FunctionMap`\ s describing what to do with events.
    :type pin_function_maps: list
    :param event_queue: A queue to put events on.
    :type event_queue: :py:class:`multiprocessing.Queue`
    """
    # set up epoll
    gpio25 = open(GPIO_INTERRUPT_DEVICE_VALUE, 'r')  # change to use 'with'?
    epoll = select.epoll()
    epoll.register(gpio25, select.EPOLLIN | select.EPOLLET)

    # a bit map showing what caused the interrupt
    intflag = INTFA if port == GPIOA else INTFB
    # a snapshot of the port when interrupt occured
    intcapture = INTCAPA if port == GPIOA else INTCAPB

    while True:
        # wait here until input
        events = epoll.poll()

        # find out where the interrupt came from and put it on the event queue
        interrupt_flag = read(intflag, board_num)
        if interrupt_flag == 0:
            continue  # The interrupt has not been flagged on this board
        else:
            interrupt_capture = read(intcapture, board_num)
            event_queue.add_event(InterruptEvent(
                interrupt_flag, interrupt_capture, board_num, time.time()))

    epoll.close()


def handle_events(
        function_maps, event_queue, event_matches_function_map,
        terminate_signal):
    """Waits for events on the event queue and calls the registered functions.

    :param function_maps: A list of classes that have inheritted from
        :class:`FunctionMap`\ s describing what to do with events.
    :type function_maps: list
    :param event_queue: A queue to put events on.
    :type event_queue: :py:class:`multiprocessing.Queue`
    :param event_matches_function_map: A function that determines if the given
        event and :class:`FunctionMap` match.
    :type event_matches_function_map: function
    :param terminate_signal: The signal that, when placed on the event queue,
        causes this function to exit.
    """
    while True:
        event = event_queue.get()
        if event == terminate_signal:
            return
        # if matching get the callback function, else function is None
        functions = map(
            lambda fm: fm.callback
            if event_matches_function_map(event, fm) else None,
            function_maps)
        # reduce to just the callback functions (remove None)
        # TODO: I think this can just be filter(None, functions)
        functions = filter(lambda f: f is not None, functions)

        for function in functions:
            function(event)


def clear_interrupts(port):
    """Clears the interrupt flags by 'read'ing the capture register
    on all boards.
    """
    intcap = INTCAPA if port == GPIOA else INTCAPB
    for i in range(MAX_BOARDS):
        read(intcap, i)


def enable_interrupts(port):
    """Enables interrupts on the port specified.

    :param port: The port to enable interrupts on
        (pifacecommon.core.GPIOA, pifacecommon.core.GPIOB)
    :type port: int
    """
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
    """Disables interrupts on the port specified.

    :param port: The port to enable interrupts on
        (pifacecommon.core.GPIOA, pifacecommon.core.GPIOB)
    :type port: int
    """
    # neither edgez
    with open(GPIO_INTERRUPT_DEVICE_EDGE, 'w') as gpio25edge:
        gpio25edge.write('none')

    # remove the pin from userspace
    with open(GPIO_UNEXPORT_FILE, 'w') as unexport_file:
        unexport_file.write(str(GPIO_INTERRUPT_PIN))

    # disable the interrupt
    int_enable_port = GPINTENA if port == GPIOA else GPINTENB
    for board_index in range(MAX_BOARDS):
        write(0, int_enable_port, board_index)
