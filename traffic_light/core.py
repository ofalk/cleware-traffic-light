from enum import IntEnum

import functools
import usb.core
import usb.util

from traffic_light.error import TrafficLightError, MultipleTrafficLightsError

BM_REQUEST_TYPE = 0x21
B_REQUEST = 0x09
W_VALUE = 0x200
W_INDEX = 0x00
ID_VENDOR = 0x0d50
ID_PRODUCT = 0x0008
INTERFACE = 0


class Color(IntEnum):
    RED = 0x10
    YELLOW = 0x11
    GREEN = 0x12


class State(IntEnum):
    OFF = 0x0
    ON = 0x1


class ClewareTrafficLight:
    def __init__(self, address=None):
        if address:
            self.address = address
            self.device = usb.core.find(
                address=address,
                idVendor=ID_VENDOR,
                idProduct=ID_PRODUCT)
        elif len(list(ClewareTrafficLight.find_devices())) > 1:
            raise MultipleTrafficLightsError(
                "No address is given and there are multiple devices conected! "
                "Use 'print_devices' to see a list of connected devices."
            )
        else:
            self.device = usb.core.find(
                idVendor=ID_VENDOR,
                idProduct=ID_PRODUCT)
        if self.device is None:
            raise TrafficLightError('Cleware traffic light not found!')
        self.reattach = False

    def attach(self):
        """Attaches the device back to the kernel"""
        usb.util.dispose_resources(self.device)
        if self.reattach:
            self.device.attach_kernel_driver(INTERFACE)

    def detach(self):
        """Detaches the device from to kernel so it can be used"""
        if self.device.is_kernel_driver_active(INTERFACE):
            self.device.detach_kernel_driver(INTERFACE)
            self.reattach = True

    @staticmethod
    def find_devices():
        """Returns the raw iterator of all found traffic lights"""
        devices = usb.core.find(find_all=True, idVendor=ID_VENDOR, idProduct=ID_PRODUCT)
        if devices:
            return devices
        return []

    @staticmethod
    def print_devices():
        """Prints a list of all connected traffic lights"""
        devices = ClewareTrafficLight.get_devices()
        for device in devices:
            print(device)

    @staticmethod
    def get_devices():
        """Returns a list of ClewareTrafficLight instances"""
        usb_devices = ClewareTrafficLight.find_devices()
        return [ClewareTrafficLight(d.address) for d in usb_devices]

    def set_led(self, color, value, timeout=1000):
        """Sets the given state and color of the attached traffic light

        Attribute:
            color -- the to set color as the enum. E.g. Color.RED
            state -- the state to which it should be set. E.g. State.ON
            address -- the usb address of a specific traffic light
        """
        try:
            self.detach()
            self.device.ctrl_transfer(BM_REQUEST_TYPE, B_REQUEST, W_VALUE, W_INDEX, [0x00, color, value], timeout=timeout)
        except Exception as exc:
            raise TrafficLightError(str(exc)) from exc
        finally:
            self.attach()

    def __getattr__(self, name):
        """Parses attribut calls in function"""
        args = name.split('_')
        try:
            color = Color[args[0].upper()]
            state = State[args[1].upper()]
        except Exception as exc:
            raise TrafficLightError("Either the given color or state could not be parsed! Exc: {}"
                                    .format(exc))
        return functools.partial(self.set_led, color, state)

    def __str__(self):
        """Converts instance into string with important imformations"""
        return ("== Cleware Traffic Light ==\n"
                "Address: {} \n"
                "IdVendor: {} \n"
                "IdProduct: {}".format(self.address, ID_VENDOR, ID_PRODUCT))
