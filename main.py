from machine import Pin, I2C
from typing import Literal, Optional
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
