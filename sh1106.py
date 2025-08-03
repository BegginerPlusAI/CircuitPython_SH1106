# The MIT License (MIT)
#
# Copyright (c) 2018 Mark Winney
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`sh1106`
====================================================

MicroPython SH1106 OLED driver, I2C and SPI interfaces

* Author(s): Mark Winney and heavily based on work by Tony DiCola, Michael McWethy
"""

import time

from micropython import const
import adafruit_framebuf

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/winneymj/Adafruit_CircuitPython_SH1106.git"

#pylint: disable-msg=bad-whitespace
# register definitions
SET_CONTRAST            = const(0x81)
SET_ENTIRE_ON           = const(0xa4)
SET_DISP_ALLON          = const(0xa5)
SET_NORM                = const(0xa6)
SET_NORM_INV            = const(0xa7)
SET_DISP_OFF            = const(0xae)
SET_DISP_ON             = const(0xaf)
SET_MEM_ADDR            = const(0x20)
SET_COL_ADDR            = const(0x21)
SET_PAGE_ADDR           = const(0x22)
SET_PAGE_ADDRESS        = const(0xb0)
SET_DISP_START_LINE = const(0x40)
SET_SEG_REMAP       = const(0xa1)
SET_MUX_RATIO       = const(0xa8)
SET_COMSCANDEC      = const(0xc8)
SET_COMSCANINC      = const(0xc0)
SET_DISP_OFFSET     = const(0xd3)
SET_COM_PIN_CFG     = const(0xda)
SET_DISP_CLK_DIV    = const(0xd5)
SET_PRECHARGE       = const(0xd9)
SET_VCOM_DESEL      = const(0xdb)
SET_CHARGE_PUMP     = const(0x8d)
SET_LOW_COLUMN      = const(0x02)
SET_HIGH_COLUMN     = const(0x00)
#pylint: enable-msg=bad-whitespace


class _SH1106:
    """Base class for SH1106 display driver"""
    def __init__(self, framebuffer, width, height, external_vcc, reset):
        self.framebuf = framebuffer
        self.fill = self.framebuf.fill
        self.pixel = self.framebuf.pixel
        self.line = self.framebuf.line
        self.text = self.framebuf.text
        self.scroll = self.framebuf.scroll
        self.blit = self.framebuf.blit
        self.vline = self.framebuf.vline
        self.hline = self.framebuf.hline
        self.fill_rect = self.framebuf.fill_rect
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.reset_pin = reset
        if self.reset_pin:
            self.reset_pin.switch_to_output(value=0)

    def poweroff(self):
        """Turn off the display (nothing visible)"""
        self.write_cmd(SET_DISP_OFF)

    def contrast(self, contrast):
        """Adjust the contrast"""
        self.write_cmd(SET_CONTRAST)
        self.write_cmd(contrast)

    def invert(self, invert):
        """Invert all pixels on the display"""
        if invert:
            self.write_cmd(SET_NORM_INV)
        else:
            self.write_cmd(SET_NORM)

    def write_framebuf(self):
        """Derived class must implement this"""
        raise NotImplementedError

    def write_cmd(self, cmd):
        """Derived class must implement this"""
        raise NotImplementedError

    def poweron(self):
        "Reset device and turn on the display."
        if self.reset_pin:
            self.reset_pin.value = 1
            time.sleep(0.001)
            self.reset_pin.value = 0
            time.sleep(0.010)
            self.reset_pin.value = 1
            time.sleep(0.010)
        self.write_cmd(SET_DISP_ON)
        
    # Zmiana w show():
    def show(self):
        """Update the display"""
        self.write_framebuf()

class SH1106_I2C(_SH1106):
    """
    I2C class for SH1106
    # ... (resztę doc string) ...
    """
    def __init__(self, width, height, i2c, *, addr=0x3c, external_vcc=False, reset=None):
        self.i2c_bus = i2c
        self.addr = addr
        self.temp = bytearray(2)
        self.buffer = bytearray(((height // 8) * width) + 1)
        self.buffer[0] = 0x40
        framebuffer = adafruit_framebuf.FrameBuffer1(memoryview(self.buffer)[1:], width, height)

        super().__init__(framebuffer, width, height, external_vcc, reset) # Wywołanie konstruktora bazowego

        # --- TERAZ CAŁA LOGIKA INICJALIZACJI IDZIE TUTAJ ---
        if self.reset_pin: # Przeniesiona logika poweron
            self.reset_pin.value = 1
            time.sleep(0.001)
            self.reset_pin.value = 0
            time.sleep(0.010)
            self.reset_pin.value = 1
            time.sleep(0.010)

        # Logika init_display (z poprzednich poprawek)
        for cmd in (
                SET_DISP_OFF, # Display Off
                SET_DISP_CLK_DIV, 0xF0, # Ratio
                SET_MUX_RATIO, 0x3F, # Multiplex
                SET_DISP_OFFSET, 0x00, # No offset
                SET_DISP_START_LINE | 0x00, # Start line
                SET_CHARGE_PUMP, 0x10 if self.external_vcc else 0x14, # Charge pump
                SET_MEM_ADDR, 0x00, # Memory mode, Horizontal
                SET_PAGE_ADDRESS, # Page address 0
                SET_COMSCANDEC, # COMSCANDEC
                SET_LOW_COLUMN | 0x02, # Ustawia początkową niską kolumnę na 2
                SET_HIGH_COLUMN | 0x00, # Ustawia początkową wysoką kolumnę na 0 (z 0x10)
                SET_COM_PIN_CFG, 0x02 if self.height == 32 else 0x12, # SETCOMPINS
                SET_CONTRAST, 0x9f if self.external_vcc else 0xcf, # Contrast maximum
                SET_SEG_REMAP, # SET_SEGMENT_REMAP
                SET_PRECHARGE, 0x22 if self.external_vcc else 0xf1, # Pre Charge
                SET_VCOM_DESEL, 0x20, # VCOM Detect 0.77*Vcc
                SET_ENTIRE_ON, # DISPLAYALLON_RESUME
                SET_NORM, # NORMALDISPLAY
                SET_DISP_ON): # on
            self.write_cmd(cmd) # Teraz self.write_cmd() odnosi się do tej klasy!

        self.fill(0) # Ta metoda jest z framebuf i działa
        self.show() # To wywoła write_framebuf() z tej klasy

    def write_cmd(self, cmd):
        """Send a command to the I2C device"""
        self.temp[0] = 0x00 # Co = 0, D/C = 0
        self.temp[1] = cmd
        self.i2c_bus.try_lock()
        self.i2c_bus.writeto(self.addr, self.temp)

    def write_framebuf(self):
        """write to the frame buffer via I2C"""
        self.i2c_bus.try_lock()
        write = self.i2c_bus.writeto
        write_cmd = self.write_cmd # Upewnij się, że używasz write_cmd z tej klasy

        for page in range(0, 8):
            write_cmd(0xB0 + page)
            write_cmd(0x02)
            write_cmd(0x10)

            data_to_send = bytearray(1 + self.width)
            data_to_send[0] = 0x40
            for i in range(self.width):
                 data_to_send[1 + i] = self.buffer[1 + (page * self.width) + i]
            write(self.addr, data_to_send)

        self.i2c_bus.unlock()

#pylint: disable-msg=too-many-arguments
class SH1106_SPI(_SH1106):
    def __init__(self, width, height, spi, dc, reset, cs, *,
                 external_vcc=False, baudrate=8000000, polarity=0, phase=0):
        # ... (pozostały kod inicjalizacyjny) ...
        framebuffer = adafruit_framebuf.FrameBuffer1(self.buffer, width, height) # Upewnij się, że FrameBuffer1 jest poprawnie zaimportowany dla SPI

        # TUTAJ PRZEKAZUJEMY REFERENCJE DO METOD TEJ KLASY
        super().__init__(framebuffer, width, height, external_vcc, reset, self.write_cmd, self.write_framebuf)

    def write_cmd(self, cmd):
        """Send a command to the SPI device"""
        self.dc_pin.value = 0
        self.spi_bus.try_lock()
        self.spi_bus.write(bytearray([cmd]))

    def write_framebuf(self):
        """write to the frame buffer via SPI"""

        self.spi_bus.try_lock()
        spi_write = self.spi_bus.write
        write = self.write_cmd

        for page in range(0, 8): # Pages
            page_mult = (page << 7)
            write(0xB0 + page) # set page address
            write(0x02) # set lower column address
            write(0x10) # set higher column address

            self.dc_pin.value = 1
            spi_write(self.buffer, start=page_mult, end=page_mult + self.width)

        self.spi_bus.unlock()
