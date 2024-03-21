from machine import Pin, I2C, Timer
from typing import Literal, Optional, Tuple, Callable, Awaitable
import utime
import uasyncio as asyncio
import ssd1306
import math

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


from typing import Tuple, Literal, Callable, Awaitable, Optional
from machine import Pin
from utime import sleep_us
import uasyncio

HIGH = True
LOW = False


class DRV8825SteppingMode:
    def __init__(
        self,
        name: str,
        mode_setting: Tuple[bool, bool, bool],
        microsteps: Literal[1, 2, 4, 8, 16, 32],
    ):
        self.name = name
        self.mode_setting = mode_setting
        self.microsteps = microsteps


class DRV8825Modes:
    FULL = DRV8825SteppingMode("FULL", (LOW, LOW, LOW), 1)
    HALF = DRV8825SteppingMode("HALF", (HIGH, LOW, LOW), 2)
    QUARTER = DRV8825SteppingMode("QUARTER", (LOW, HIGH, LOW), 4)
    ONE_8 = DRV8825SteppingMode("1/8", (HIGH, HIGH, LOW), 8)
    ONE_16 = DRV8825SteppingMode("1/16", (LOW, LOW, HIGH), 16)
    ONE_32 = DRV8825SteppingMode("1/32", (HIGH, LOW, HIGH), 32)


class DRV8825StepperMotor:
    # https://www.studiopieters.nl/drv8825-pinout/

    def __init__(
        self,
        step_pin: Pin,
        direction_pin: Optional[Pin] = None,
        reset_pin: Optional[Pin] = None,
        sleep_pin: Optional[Pin] = None,
        enable_pin: Optional[Pin] = None,
        mode_pins: Optional[Tuple[Pin, Pin, Pin]] = None,
        fault_pin: Optional[Pin] = None,
        mode: DRV8825SteppingMode = DRV8825Modes.FULL,
        full_steps_for_one_revolution: int = 200,
        target_time_for_one_revolution_ms: float = 500,
        skip_motor_init: bool = False,
    ):
        """Init function for DRV8825StepperMotor

        Args:
            step_pin (Pin): board gpio that connect to the drv8825 STP pin
            direction_pin (Optional[Pin], optional): board gpio that connect to the drv8825 DIR pin. Defaults to None.
            reset_pin (Optional[Pin], optional): board gpio that connect to the drv8825 RST pin. Defaults to None.
            sleep_pin (Optional[Pin], optional): board gpio that connect to the drv8825 SLP pin. Defaults to None.
            enable_pin (Optional[Pin], optional): board gpio that connect to the drv8825 EN pin. Defaults to None.
            mode_pins (Optional[Tuple[Pin, Pin, Pin]], optional): Tuple of board gpio pins that connect to the drv8225s M0, M1, M2 pin. Defaults to None.
            fault_pin (Optional[Pin], optional): board gpio that connect to the drv8825 FLT pin. Defaults to None.
            mode (Optional[DRV8825SteppingMode], optional): Microstepping mode defined in class `DRV8825Modes`. Defaults to DRV8825Modes.FULL
            full_steps_for_one_revolution (Optional[int], optional): Amount of steps needed for a fill revolution in FULL step mode. Depends on the motor you are using. Look up in the specs. Defaults to 200.. Defaults to 200.
            target_time_for_one_revolution_ms (Optional[float], optional): Translates into speed. We try to match the target time but can not guarante it. Defaults to 500.. Defaults to 500.
            skip_motor_init (Optional[bool], optional): if set to true and the respective pins are provided the motor will be enabled, un-reseted, un-sleeped and the stepper mode will be set. If set to False you need to prepare the motor yourself.
        """
        self.step_pin = step_pin
        self.direction_pin = direction_pin
        self.reset_pin = reset_pin
        self.sleep_pin = sleep_pin
        self.enable_pin = enable_pin
        self.mode_pins = mode_pins
        self.fault_pin = fault_pin
        self.full_steps_for_one_revolution = full_steps_for_one_revolution
        self.target_time_for_one_revolution_ms = target_time_for_one_revolution_ms
        self.mode = mode

        self.pulse_delay_us: float = 0.0
        self.steps_for_one_revolution = 0
        if not skip_motor_init:
            self._init_motor()

    def _init_motor(self):
        if self.enable_pin:
            self.enable()
        if self.reset_pin:
            self.reset(False)
        if self.sleep_pin:
            self.sleep(False)
        self.set_mode(self.mode)

    def set_mode(self, mode: DRV8825SteppingMode):
        """All modes are defined in DRV8825Modes

        Args:
            res (Tuple[bool, bool, bool]): _description_
        """
        # Calcuate pulse delay time (Wait time before triggering the next motor step aka. energizing to next the coil)
        self.steps_for_one_revolution = self.mode.microsteps * (
            self.full_steps_for_one_revolution
        )

        delay_ms = self.target_time_for_one_revolution_ms / int(
            self.steps_for_one_revolution * 2
        )

        ## the pulse delay offset value is not based on anything. it just works ¯\_(ツ)_/¯.
        ## The resulting time for one revolution is in all my test cases closer to self.target_time_for_one_revolution_ms as without
        ## (ToDo: find explanation)
        pulse_delay_offset = self.mode.microsteps
        self.pulse_delay_us = int(delay_ms * 1000) - pulse_delay_offset

        # Set the microstepping on the DRV8825 driver
        if self.mode_pins and len(self.mode_pins) == 3:
            for index, pin in enumerate(self.mode_pins):
                pin.value(mode.mode_setting[index])
        else:
            print(
                f"Warning: Microstepping mode set to {mode.name}, but mode pin (M0,M1,M3) were not provided. Make sure mode pins are set otherwise."
            )
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
        if self.enable_pin:
            self.enable_pin.value(not enable)
        else:
            raise ValueError(
                "Can not switch EN pin. Pin was not provided on instantiation of `DRV8825StepperMotor`."
            )

    def sleep(self, sleep_: bool = True):
        """Set the driver in "sleep"-mode (or disable sleep mode)"""
        # from https://lastminuteengineers.com/drv8825-stepper-motor-driver-arduino-tutorial/
        """SLP is an active low input pin.
        Pulling this pin LOW puts the driver into sleep mode,
        reducing power consumption to a minimum.
        You can use this to save power, especially when the motor is not in use."""
        if self.sleep_pin:
            self.sleep_pin.value(not sleep_)
        else:
            raise ValueError(
                "Can not switch SLP pin. Pin was not provided on instantiation of `DRV8825StepperMotor`."
            )

    def reset(self, reset: bool = False):
        """Activate or disable reset mode"""
        # from https://lastminuteengineers.com/drv8825-stepper-motor-driver-arduino-tutorial/
        """RST is an active low input as well. 
        When this pin is pulled LOW, all STEP inputs are ignored. 
        It also resets the driver by setting the internal translator to a predefined “home” state. 
        Home state is basically the initial position from which the motor starts, 
        and it varies based on microstep resolution.
        """
        if self.reset_pin:
            self.reset_pin.value(not reset)
        else:
            raise ValueError(
                "Can not switch RST pin. Pin was not provided on instantiation of `DRV8825StepperMotor`."
            )

    def direction_clockwise(self, clockwise: Optional[bool] = True):
        """If set True the motor will turn clockwise. Otherwise counterclockwise

        Args:
            clockwise (bool, optional): _description_. Defaults to True.
        """
        # from https://lastminuteengineers.com/drv8825-stepper-motor-driver-arduino-tutorial/
        """
        DIR input controls the spinning direction of the motor. Pulling it HIGH turns the motor clockwise, while pulling it LOW turns it counterclockwise.
        """
        if self.direction_pin:
            self.direction_pin.value(clockwise)
        else:
            raise ValueError(
                "Can not switch DIR pin. Pin was not provided on instantiation of `DRV8825StepperMotor`."
            )

    def step(self, steps: int = 1, clockwise: Optional[bool] = None):
        """Turn the motor one step

        Args:
            steps (int, optional): _description_. Defaults to 1.
            clockwise (bool, optional): _description_. Defaults to None.
        """
        if clockwise:
            self.direction_clockwise(clockwise)
        for i in range(steps * 2):
            sleep_us(self.pulse_delay_us)
            self.step_pin.value(not self.step_pin.value())

    def rotate(self, revolutions: float = 1.0, clockwise: Optional[bool] = None):
        """Turn the motor X revolutions (One revolution -> 360°). Can be a float to turn fractional revolution (1.5 will make one and a half revolution)

        Args:
            rotations (float, optional): _description_. Defaults to 1.0.
            clockwise (bool, optional): _description_. Defaults to False.
        """
        self.step(
            steps=int(self.steps_for_one_revolution * revolutions),
            clockwise=clockwise,
        )

    def rotate_while(
        self, while_check_func: Callable[[], bool], clockwise: Optional[bool] = None
    ):
        """Provide a function that returns a boolean. The motor will rotate until the function returns False.
        example:
        ```python
        def button_is_pressed() -> bool:
            return my_button_pin.value()
        m.rotate_while(button_is_pressed)
        ```
        Args:
            while_check_func (Callable[[], bool]): _description_
            clockwise (bool, optional): _description_. Defaults to None.
        """
        if clockwise:
            self.direction_clockwise(clockwise)
        while while_check_func():
            self.step(1, clockwise)

    async def async_step(self, steps: int = 1, clockwise: Optional[bool] = None):
        """Same as

        Args:
            steps (int, optional): _description_. Defaults to 1.
            clockwise (bool, optional): _description_. Defaults to False.
        """
        if clockwise:
            self.direction_clockwise(clockwise)
        for i in range(steps * 2):
            await uasyncio.sleep_us(self.pulse_delay_us)
            self.step_pin.value(not self.step_pin.value())

    async def async_rotate(
        self, rotations: float = 1.0, clockwise: Optional[bool] = False
    ):
        await self.async_step(
            steps=int(self.steps_for_one_revolution * rotations),
            clockwise=clockwise,
        )

    async def async_rotate_while(
        self,
        while_check_func: Callable[[], Awaitable[bool]],
        clockwise: Optional[bool] = None,
    ):
        """Provide a async function that returns a boolean. The motor will rotate until the function returns False.
        example:
        ```python
        import uasyncio
        start_time = utime.ticks_ms()
        async def are_3_seconds_gone() -> bool:
            if (utime.ticks_diff(utime.ticks_ms(), start_time) / 1000) > 3:
                return True
            return False
        uasyncio.run(m.async_rotate_while(are_3_seconds_gone, clockwise=False))
        ```
        Args:
            while_check_func (Callable[[], Awaitable[bool]]): _description_
            clockwise (bool, optional): _description_. Defaults to None.
        """
        if clockwise:
            self.direction_clockwise(clockwise)
        res = await while_check_func()
        print("RES", res)
        while not await while_check_func():
            self.step(1, clockwise)


m = DRV8825StepperMotor(
    step_pin=Pin(4, Pin.OUT),
    direction_pin=Pin(5, Pin.OUT),
    reset_pin=Pin(2, Pin.OUT),
    sleep_pin=Pin(3, Pin.OUT),
    enable_pin=Pin(6, Pin.OUT),
    mode_pins=(Pin(7, Pin.OUT), Pin(8, Pin.OUT), Pin(9, Pin.OUT)),
    mode=DRV8825Modes.ONE_16,
    target_time_for_one_revolution_ms=300,
)
import utime

"""
start = utime.ticks_ms()
# m.enable()
m.rotate(1.0, False)
end = utime.ticks_ms()
dur = utime.ticks_diff(end, start) / 1000
print("Duration sec:", dur)
# m.rotate(20, False)
m.sleep()
"""


# async example
import uasyncio

start_time = utime.ticks_ms()


async def three_seconds_are_gone() -> bool:
    if (utime.ticks_diff(utime.ticks_ms(), start_time) / 1000) > 3:
        return True
    return False


uasyncio.run(m.async_rotate_while(three_seconds_are_gone, clockwise=False))
m.sleep()
