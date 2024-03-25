from machine import Pin, I2C
from typing import Literal, Optional, Tuple, Callable, Awaitable
import utime
import uasyncio
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


from typing import Tuple, Literal, Callable, Awaitable, Optional, Dict, Any
from machine import Pin, Timer
from utime import sleep_us
import uasyncio


class DRV8825StepperMotor:
    # https://www.studiopieters.nl/drv8825-pinout/
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

    MODE_FULL = DRV8825SteppingMode("FULL", (LOW, LOW, LOW), 1)
    MODE_HALF = DRV8825SteppingMode("HALF", (HIGH, LOW, LOW), 2)
    MODE_QUARTER = DRV8825SteppingMode("QUARTER", (LOW, HIGH, LOW), 4)
    MODE_ONE_8 = DRV8825SteppingMode("1/8", (HIGH, HIGH, LOW), 8)
    MODE_ONE_16 = DRV8825SteppingMode("1/16", (LOW, LOW, HIGH), 16)
    MODE_ONE_32 = DRV8825SteppingMode("1/32", (HIGH, LOW, HIGH), 32)

    class NonBlockResult:
        def __init__(self):
            self.done = False
            self.pulses_done: int = 0
            self._start_tick_ms: Optional[float] = None
            self._finish_tick_ms: Optional[float] = None
            self.callback_result: Any = None

        def get_run_time_ms(self) -> float:
            if self._start_tick_ms is None:
                raise ValueError("Non blocking function not yet started.")
            if self._finish_tick_ms is None:
                return utime.ticks_diff(utime.ticks_ms(), self._start_tick_ms)
            return utime.ticks_diff(self._finish_tick_ms, self._start_tick_ms)

        def get_steps_done(self) -> float:
            return self.pulses_done / 2

    class NonBlockTimerContainer:

        def __init__(
            self,
            timer: Timer,
            target_steps: Optional[int] = None,
            keep_running_check_callback: Optional[Callable[[], bool]] = None,
            finished_callback: Optional[
                Optional[
                    Callable[
                        ["DRV8825StepperMotor.NonBlockResult"],
                        "DRV8825StepperMotor.NonBlockResult",
                    ]
                ]
            ] = None,
        ):
            if target_steps and keep_running_check_callback:
                raise ValueError(
                    f"Either set 'target_steps' or 'keep_running_check_callback', not both."
                )
            elif not target_steps and not keep_running_check_callback:
                raise ValueError(
                    f"Either set 'target_steps' or 'keep_running_check_callback'."
                )
            self.timer = timer
            self.steps_remaining = target_steps
            self.keep_running_check_callback = keep_running_check_callback
            self.finished_callback = finished_callback
            self.result = DRV8825StepperMotor.NonBlockResult()

        def make_pulse(self) -> bool:
            if self.result._start_tick_ms is None:
                self.result._start_tick_ms = utime.ticks_ms()
            result = False

            if self.keep_running_check_callback is not None:
                result = self.keep_running_check_callback()
            elif self.steps_remaining == 0:
                result = False
            elif self.steps_remaining:
                self.steps_remaining = self.steps_remaining - 1
                result = True
            if result:
                self.result.pulses_done = self.result.pulses_done + 1
            # just to make the linter happy.
            return result

        def finish(self) -> "DRV8825StepperMotor.NonBlockResult":
            self.timer.deinit()
            self.result._finish_tick_ms = utime.ticks_ms()
            self.result.done = True
            if self.finished_callback:
                self.result.callback_result = self.finished_callback(self.result)
            return self.result

    def __init__(
        self,
        step_pin: Pin,
        direction_pin: Optional[Pin] = None,
        reset_pin: Optional[Pin] = None,
        sleep_pin: Optional[Pin] = None,
        enable_pin: Optional[Pin] = None,
        mode_pins: Optional[Tuple[Pin, Pin, Pin]] = None,
        fault_pin: Optional[Pin] = None,
        mode: DRV8825SteppingMode = MODE_FULL,
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
        self._timer_container: Optional[DRV8825StepperMotor.NonBlockTimerContainer] = (
            None
        )

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
        self.pulse_delay_us = int(delay_ms * 1000)

        ## the pulse delay offset value is not based on anything. it just works in blocking functions ¯\_(ツ)_/¯
        ## The resulting time for one revolution is in all my test cases closer to self.target_time_for_one_revolution_ms as without
        # it is not used in non blocking (incl. asynco) functions
        ## (ToDo: find explanation and document)
        self.pulse_delay_offset_blocking_step = -self.mode.microsteps

        # Set the microstepping on the DRV8825 driver
        if self.mode_pins and len(self.mode_pins) == 3:
            for index, pin in enumerate(self.mode_pins):
                pin.value(mode.mode_setting[index])
        else:
            print(
                f"Warning: Microstepping mode set to {mode.name}, but mode pins (M0,M1,M3) were not provided. Make sure mode pins are set otherwise/externaly."
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

    def is_direction_clockwise(self) -> bool:
        """Check current set roatation direction of motor

        Raises:
            ValueError: Fails if DIR pin is not provided

        Returns:
            bool: _description_
        """
        if self.direction_pin:
            return bool(self.direction_pin.value())
        else:
            raise ValueError(
                "Can determine direction. DIR pin was not provided on instantiation of `DRV8825StepperMotor`."
            )

    def step(self):
        """Create a single pulse on the STP pin. A.k.a make one step."""
        self.step_pin.toggle()

    def steps(self, amount: int = 1, clockwise: Optional[bool] = None):
        """Turn the motor one step. This is the most simple method but also a blocking one.
        It is easy to understand but comes with some caveats:
            * The speed can vary based the work load of the microcontroller.
            * You can not do anything else until the motor movement is finished.
        If you need a non blocking way have a look at DRV8825StepperMotor.steps_non_blocking() and/or DRV8825StepperMotor.steps_async()

        Args:
            amount (int, optional): _description_. Defaults to 1.
            clockwise (bool, optional): _description_. Defaults to None.
        """
        if clockwise:
            self.direction_clockwise(clockwise)
        for i in range(amount * 2):
            sleep_us(self.pulse_delay_us + self.pulse_delay_offset_blocking_step)
            self.step()

    def rotate(
        self,
        revolutions: float = 1.0,
        clockwise: Optional[bool] = None,
    ):
        """Turn the motor X revolutions (One revolution -> 360°). Can be a float to turn fractional revolution (1.5 will make one and a half revolution)
        This is a blocking function, see DRV8825StepperMotor.steps() to be aware of the caveats.

        Args:
            revolutions (float, optional): _description_. Defaults to 1.0.
            clockwise (bool, optional): _description_. Defaults to False.
        """
        step_count = int(self.steps_for_one_revolution * revolutions)
        self.steps(
            amount=step_count,
            clockwise=clockwise,
        )

    def rotate_while(
        self, while_check_func: Callable[[], bool], clockwise: Optional[bool] = None
    ):
        """Provide a function that returns a boolean. The motor will rotate until the function returns False.
        Args:
            while_check_func (Callable[[], bool]): _description_
            clockwise (bool, optional): _description_. Defaults to None.
        """
        if clockwise:
            self.direction_clockwise(clockwise)
        while while_check_func():
            self.steps(1)

    def _step_non_blocking_timer_callback(self, t: Timer):
        if self._timer_container:
            if self._timer_container.make_pulse():
                self.step()
            else:
                self._timer_container.finish()

    def _steps_non_blocking(
        self, timer_container: NonBlockTimerContainer, clockwise: Optional[bool] = None
    ):
        if clockwise:
            self.direction_clockwise(clockwise)

        self._timer_container = timer_container
        # Micropython Timers frequencies are defined in hertz(hz). Lets first calculate our delay into Hz.
        frequency_hz: int = int((1 / (self.pulse_delay_us / 1000 / 1000)))

        self._timer_container.timer.init(
            freq=frequency_hz,
            mode=Timer.PERIODIC,
            callback=self._step_non_blocking_timer_callback,
        )
        return self._timer_container.result

    def steps_non_blocking(
        self,
        amount: int = 1,
        clockwise: Optional[bool] = None,
        callback: Optional[Callable[[NonBlockResult], Any]] = None,
        timer_id: int = -1,
    ) -> NonBlockResult:
        """Do x steps. Same as DRV8825StepperMotor.steps(), but non blocking.
        This means you can call this function and the code will continue and not wait for the motor move to be finished.
        The non blocking behaviour is achieved by using a Machine.Timer().

        Args:
            steps (int, optional): _description_. Defaults to 1.
            clockwise (Optional[bool], optional): _description_. Defaults to None.
            callback (Optional[Callable], optional): _description_. Defaults to None.
            timer_id (int, optional): _description_. Defaults to -1.
        """
        non_block_timer_container = DRV8825StepperMotor.NonBlockTimerContainer(
            timer=Timer(timer_id),
            target_steps=amount * 2,
            finished_callback=callback,
        )
        return self._steps_non_blocking(
            timer_container=non_block_timer_container,
            clockwise=clockwise,
        )

    def rotate_non_blocking(
        self,
        revolutions: float = 1.0,
        clockwise: Optional[bool] = None,
        callback: Optional[Callable[[NonBlockResult], Any]] = None,
        timer_id: int = -1,
    ) -> NonBlockResult:
        """Do x revolutions. Same as DRV8825StepperMotor.rotate(), but non blocking.
        This means you can call this function and the code will continue and not wait for the motor move to be finished.
        The non blocking behaviour is achieved by using a Machine.Timer().

        Args:
            revolutions (float, optional): _description_. Defaults to 1.0.
            clockwise (Optional[bool], optional): _description_. Defaults to None.
            callback (Optional[Callable], optional): _description_. Defaults to None.
            timer_id (int, optional): _description_. Defaults to -1.
        """
        step_count = int(self.steps_for_one_revolution * revolutions)
        return self.steps_non_blocking(
            amount=step_count,
            clockwise=clockwise,
            timer_id=timer_id,
            callback=callback,
        )

    def rotate_while_non_blocking(
        self,
        while_check_func: Callable[[], bool],
        clockwise: Optional[bool] = None,
        callback: Optional[Callable[[NonBlockResult], Any]] = None,
        timer_id: int = -1,
    ) -> NonBlockResult:
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

        return self._steps_non_blocking(
            timer_container=DRV8825StepperMotor.NonBlockTimerContainer(
                timer=Timer(timer_id),
                keep_running_check_callback=while_check_func,
                finished_callback=callback,
            )
        )

    async def step_async(self, steps: int = 1, clockwise: Optional[bool] = None):
        """Async (uasyncio) version of DRV8825StepperMotor.step()


        Args:
            steps (int, optional): _description_. Defaults to 1.
            clockwise (bool, optional): _description_. Defaults to None.
        """
        if clockwise:
            self.direction_clockwise(clockwise)
        for i in range(steps * 2):
            await uasyncio.sleep_ms(self.pulse_delay_us / 1000)
            self.step()

    async def rotate_async(
        self, revolutions: int | float = 1.0, clockwise: bool = False
    ):
        """Async (uasyncio) version of DRV8825StepperMotor.rotate()
        Turn the motor X revolutions (One revolution -> 360°). Can be a float to turn fractional revolution (1.5 will make one and a half revolution)

        Args:
            rotations (float, optional): _description_. Defaults to 1.0.
            clockwise (bool, optional): _description_. Defaults to False.
        """
        await self.step_async(
            steps=int(self.steps_for_one_revolution * revolutions),
            clockwise=clockwise,
        )

    async def rotate_while_async(
        self,
        while_check_func: Callable[[], Awaitable[bool]],
        clockwise: Optional[bool] = None,
    ):
        """Provide a async function that returns a boolean. The motor will rotate until the function returns False.
        example:
        Args:
            while_check_func (Callable[[], Awaitable[bool]]): _description_
            clockwise (bool, optional): _description_. Defaults to None.
        """
        if clockwise:
            self.direction_clockwise(clockwise)
        while not await while_check_func():
            self.steps(1, clockwise)


m = DRV8825StepperMotor(
    step_pin=Pin(4, Pin.OUT),
    direction_pin=Pin(5, Pin.OUT),
    reset_pin=Pin(2, Pin.OUT),
    sleep_pin=Pin(3, Pin.OUT),
    enable_pin=Pin(6, Pin.OUT),
    mode_pins=(Pin(7, Pin.OUT), Pin(8, Pin.OUT), Pin(9, Pin.OUT)),
    mode=DRV8825StepperMotor.MODE_ONE_8,
    target_time_for_one_revolution_ms=1000,
)
button = Pin(15, Pin.IN, pull=1)


async def button_is_pressed():
    return bool(not button.value())


import uasyncio

uasyncio.run(m.rotate_while_async(button_is_pressed, clockwise=True))
"""
m = DRV8825StepperMotor(
    step_pin=Pin(4, Pin.OUT),
    direction_pin=Pin(5, Pin.OUT),
    reset_pin=Pin(2, Pin.OUT),
    sleep_pin=Pin(3, Pin.OUT),
    enable_pin=Pin(6, Pin.OUT),
    mode_pins=(Pin(7, Pin.OUT), Pin(8, Pin.OUT), Pin(9, Pin.OUT)),
    target_time_for_one_revolution_ms=1000,
)
m.rotate(3, clockwise=False)
m.sleep()


print("GO")
m = DRV8825StepperMotor(
    step_pin=Pin(4, Pin.OUT),
    direction_pin=Pin(5, Pin.OUT),
    reset_pin=Pin(2, Pin.OUT),
    sleep_pin=Pin(3, Pin.OUT),
    enable_pin=Pin(6, Pin.OUT),
    mode_pins=(Pin(7, Pin.OUT), Pin(8, Pin.OUT), Pin(9, Pin.OUT)),
    mode=DRV8825StepperMotor.MODE_ONE_32,
    target_time_for_one_revolution_ms=2000,
)
# m.steps(100)
print("TIMER")
# m.steps_non_blocking(1000)
from time import sleep

start_time = utime.ticks_ms()


def print_time_gone():
    print(utime.ticks_diff(utime.ticks_ms(), start_time), "ms")


def reset_start_time():
    global start_time
    start_time = utime.ticks_ms()


m.rotate(5)
print_time_gone()
reset_start_time()
m.rotate_non_blocking(5, callback=print_time_gone)
print("Do other stuff while the motor is rotating")
sleep(12)

m.sleep()


start_time = utime.ticks_ms()

m.rotate(1, clockwise=True)


def three_seconds_are_gone() -> bool:
    if (utime.ticks_diff(utime.ticks_ms(), start_time) / 1000) > 3:
        return True
    return False


m.rotate_while(three_seconds_are_gone, clockwise=False)
m.sleep()
exit()
import machine


class Servo:
    def __init__(
        self, pin_id, min_us=544.0, max_us=2400.0, min_deg=0.0, max_deg=180.0, freq=50
    ):
        self.pwm = machine.PWM(machine.Pin(pin_id))
        self.pwm.freq(freq)
        self.current_us = 0.0
        self._slope = (min_us - max_us) / (
            math.radians(min_deg) - math.radians(max_deg)
        )
        self._offset = min_us

    def write(self, deg):
        self.write_rad(math.radians(deg))

    def read(self):
        return math.degrees(self.read_rad())

    def write_rad(self, rad):
        self.write_us(rad * self._slope + self._offset)

    def read_rad(self):
        return (self.current_us - self._offset) / self._slope

    def write_us(self, us):
        self.current_us = us
        self.pwm.duty_ns(int(self.current_us * 1000.0))

    def read_us(self):
        return self.current_us

    def off(self):
        self.pwm.duty_ns(0)


s = Servo(16)
print("Turn")
s.write(200)
"""
