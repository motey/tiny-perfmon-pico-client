# tiny-perfmon-pico-client


# prepare

## Install MicroPython on Pico

Download micropython from https://micropython.org/download/RPI_PICO/

drag and drop file onto pico.

## Install mpremote for lib installing

`pip install mpremote`

## Install Libs


### ssd1306 - mini oled screen lib

`mpremote a1 mip install ssd1306`
### typing support

https://micropython-stubs.readthedocs.io/en/stable/_typing_mpy.html

`mpremote a1 mip install github:josverl/micropython-stubs/mip/typing.mpy`

`mpremote a1 mip install github:josverl/micropython-stubs/mip/typing_extensions.mpy`

pip install git+https://github.com/stlehmann/micropython-ssd1306

### local code completion for external libs

pip install -U  micropython-rp2-pico-stubs

./download_libs_for_codecompletion.sh