from machine import Pin, I2C, Timer
from typing import Literal, Optional, Tuple
import time

import ssd1306

# using default address 0x3C

i2c = I2C(id=0, sda=Pin(20), scl=Pin(21))

display_w = 128
display_h = 32
display = ssd1306.SSD1306_I2C(display_w, display_h, i2c)
row_height = 8


class InfoCell:
    def __init__(
        self,
        value: Optional[str | int] = None,
        unit: Optional[str] = None,
        size: int = 4,
    ):
        if isinstance(value, int):
            value = str(value)
        self.value: str = value if value else ""
        self.unit: str = unit if unit else ""
        self.size: int = size

    def gen(self) -> str:
        """Output value+unit str and pad to self.size on the right side of the value

        Returns:
            str: _description_
        """
        total_len = len(self.value) + len(self.unit)
        value: str = self.value
        if total_len > self.size:
            # Value to large to render. instead of crashing or showing wrong values (cut off strings) we just show some hashes "###"
            value = ""
            for i in range(1, total_len - len(self.unit)):

                value = value + "#"
        elif total_len < self.size:
            pad = ""
            for i in range(total_len, self.size):
                pad = pad + " "
            value = pad + value
        output = "{}{}".format(value if value else "", self.unit if self.unit else "")
        return output


class InfoRow:
    def __init__(self, title: str, row: Literal[0, 1, 2, 3]):
        if len(title) > 3:
            raise ValueError("Title length max is 3 chars. got {}".format(len(title)))
        self.title = title
        self.row = row
        self._x_bottom = self.row * 8
        self.cell_1: InfoCell = InfoCell()
        self.cell_2: InfoCell = InfoCell()
        self.warn_enabled: bool = False

    def write_cell_1(self, c: InfoCell):
        self.cell_1 = c

    def write_cell_2(self, c: InfoCell):
        self.cell_2 = c

    def warn(self, on: bool = True):
        self.warn_enabled = on

    def draw_warn(self):
        # Define triangle coordinates
        right_padding = 2
        width = 8
        x_bottom = self.row * row_height

        # top/peak point
        x1, y1 = (display_w - right_padding) - int(width / 2), x_bottom - row_height
        # right corner point
        x2, y2 = (display_w - right_padding), x_bottom
        # left corner point
        x3, y3 = (display_w - right_padding) - width, x_bottom

        # right triangle side
        display.line(x1, y1, x2, y2, 1)
        # bottom triangle side
        display.line(x2, y2, x3, y3, 1)
        # left triangle side
        display.line(x3, y3, x1, y1, 1)

        # bang !
        bx1, by1 = (display_w - right_padding) - int(width / 2), (
            x_bottom - int(row_height * 0.3)
        )
        bx2, by2 = (display_w - right_padding) - int(width / 2), (
            x_bottom - int(row_height * 0.6)
        )
        display.line(bx1, by1, bx2, by2, 1)

    def render(self):
        output = "{}: {} {}".format(self.title, self.cell_1.gen(), self.cell_2.gen())
        display.text(output, 0, self._x_bottom, 1)
        if self.warn_enabled:
            self.draw_warn()


cpu = InfoRow("CPU", 0)
gpu = InfoRow("GPU", 1)
mem = InfoRow("MEM", 2)
hdd = InfoRow("HDD", 3)

cpu.write_cell_1(InfoCell(100, "C"))
cpu.write_cell_2(InfoCell(100, "%"))

gpu.write_cell_1(InfoCell(1, "C"))
gpu.write_cell_2(InfoCell(98, "%"))

mem.write_cell_1(InfoCell(6, "C"))
mem.write_cell_2(InfoCell(1000, "%"))

hdd.write_cell_1(InfoCell(1000, "MB/s", 8))

hdd.warn()
gpu.warn()

cpu.render()
gpu.render()
mem.render()
hdd.render()
display.show()


def info():
    display.text("CPU: 100C 100%", 0, 0, 1)
    display.text("GPU: 100C 100%", 0, 8, 1)
    display.text("Mem: 100C 100%", 0, 16, 1)
    display.text("HDD: 100MB/s", 0, 24, 1)


def warn(row: int):
    # Define triangle coordinates (change as needed)
    # Define triangle coordinates
    right_padding = 2

    width = 8
    height = 8
    x_bottom = row * height

    # top/peak point
    x1, y1 = (display_w - right_padding) - int(width / 2), x_bottom - height
    # right corner point
    x2, y2 = (display_w - right_padding), x_bottom
    # left corner point
    x3, y3 = (display_w - right_padding) - width, x_bottom

    # right triangle side
    display.line(x1, y1, x2, y2, 1)
    # bottom triangle side
    display.line(x2, y2, x3, y3, 1)
    # left triangle side
    display.line(x3, y3, x1, y1, 1)

    # bang !
    bx1, by1 = (display_w - right_padding) - int(width / 2), (
        x_bottom - int(height * 0.3)
    )
    bx2, by2 = (display_w - right_padding) - int(width / 2), (
        x_bottom - int(height * 0.6)
    )
    display.line(bx1, by1, bx2, by2, 1)


def test_demo():
    display.fill(0)
    display.fill_rect(0, 0, 32, 32, 1)
    display.fill_rect(2, 2, 28, 28, 0)
    display.vline(9, 8, 22, 1)
    display.vline(16, 2, 22, 1)
    display.vline(23, 8, 22, 1)
    display.fill_rect(26, 24, 2, 4, 1)
    display.text("Hallo Maike", 40, 0, 1)
    display.text("I love You", 40, 12, 1)
    display.text(":)", 40, 24, 1)
    display.show()
    print("END")

    #############
    ###Motor


from time import sleep
from utime import sleep_ms

HIGH = True
LOW = False


class DRV8825Mode:
    def __init__(
        self,
        mode_setting: Tuple[bool, bool, bool],
        microsteps: Literal[1, 2, 4, 8, 16, 32],
    ):
        self.mode_setting = mode_setting
        self.microsteps = microsteps


class DRV8825Modes:
    FULL = DRV8825Mode((LOW, LOW, LOW), 1)
    HALF = DRV8825Mode((HIGH, LOW, LOW), 2)
    QUARTER = DRV8825Mode((LOW, HIGH, LOW), 4)
    ONE_8 = DRV8825Mode((HIGH, HIGH, LOW), 8)
    ONE_16 = DRV8825Mode((LOW, LOW, HIGH), 16)
    ONE_32 = DRV8825Mode((HIGH, LOW, HIGH), 32)


class DRV8825StepperMotor:
    # https://www.studiopieters.nl/drv8825-pinout/

    def __init__(
        self,
        step_pin: Pin,
        direction_pin: Pin,
        reset_pin: Pin,
        sleep_pin: Pin,
        enable_pin: Pin,
        mode_pins: Tuple[Pin, Pin, Pin],
        # fault_pin: Pin,
        mode: DRV8825Mode = DRV8825Modes.FULL,
    ):
        self.step_pin = step_pin
        self.direction_pin = direction_pin
        self.reset_pin = reset_pin
        self.sleep_pin = sleep_pin
        self.enable_pin = enable_pin
        self.mode_pins = mode_pins
        # self.fault_pin = fault_pin
        self.mode = mode
        self.delay: float = 0.0
        self._init_motor()

    def _init_motor(self):
        self.enable()
        self.reset(False)
        self.sleep(False)
        self.set_mode(self.mode)

    def set_mode(self, mode: DRV8825Mode):
        """All modes are defined in DRV8825Resolution

        Args:
            res (Tuple[bool, bool, bool]): _description_
        """
        self.delay = 0.005 / mode.microsteps
        for index, pin in enumerate(self.mode_pins):
            pin.value(mode.mode_setting[index])
        self.mode = mode

    def enable(self, enable: bool = True):
        """Enable or disable the driver"""
        # from https://lastminuteengineers.com/drv8825-stepper-motor-driver-arduino-tutorial/
        """EN is an active low input pin.
        When this pin is pulled LOW, the DRV8825 driver is enabled.
        By default, this pin is pulled low, so unless you pull it high,
        the driver is always enabled.
        This pin is particularly useful when implementing an emergency stop or shutdown system.
        """
        self.enable_pin.value(not enable)

    def sleep(self, sleep_: bool = True):
        """Set the driver in "sleep"-mode (or disable sleep mode)"""
        # from https://lastminuteengineers.com/drv8825-stepper-motor-driver-arduino-tutorial/
        """SLP is an active low input pin.
        Pulling this pin LOW puts the driver into sleep mode,
        reducing power consumption to a minimum.
        You can use this to save power, especially when the motor is not in use."""
        self.sleep_pin.value(not sleep_)

    def reset(self, reset: bool = False):
        """Activate or disable reset mode"""
        # from https://lastminuteengineers.com/drv8825-stepper-motor-driver-arduino-tutorial/
        """RST is an active low input as well. 
        When this pin is pulled LOW, all STEP inputs are ignored. 
        It also resets the driver by setting the internal translator to a predefined “home” state. 
        Home state is basically the initial position from which the motor starts, 
        and it varies based on microstep resolution.
        """
        self.reset_pin.value(not reset)

    def move(self, steps: int = 1, clockwise: bool = False):
        self.direction_pin.value(clockwise)
        # self.delay = 0.001
        self.debug_print()
        for i in range(steps * 2):
            self.step_pin.value(not self.step_pin.value())
            sleep(self.delay)
            print("self.step_pin.value", self.step_pin.value())

    def debug_print(self):
        mode_pin_values = []
        for mp in self.mode_pins:
            mode_pin_values.append(mp.value())
        output = f"step_pin = {self.step_pin.value()}\n"
        output += f"direction_pin = {self.direction_pin.value()}\n"
        output += f"reset_pin = {self.reset_pin.value()}\n"
        output += f"sleep_pin = {self.sleep_pin.value()}\n"
        output += f"enable_pin = {self.enable_pin.value()}\n"
        output += f"mode_pins = {mode_pin_values}\n"
        output += f"mode_microsteps = {self.mode.microsteps}\n"
        output += f"delay = {self.delay}"

        print(output)


m = DRV8825StepperMotor(
    step_pin=Pin(4, Pin.OUT),
    direction_pin=Pin(5, Pin.OUT),
    reset_pin=Pin(2, Pin.OUT),
    sleep_pin=Pin(3, Pin.OUT),
    enable_pin=Pin(6, Pin.OUT),
    mode_pins=(Pin(7, Pin.OUT), Pin(8, Pin.OUT), Pin(9, Pin.OUT)),
    mode=DRV8825Modes.FULL,
)

# m.enable()
m.move(200, True)
m.sleep()
