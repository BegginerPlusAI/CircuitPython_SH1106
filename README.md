CircuitPython driver for SH1106 OLED displays.

Works with CircuitPython V 9.x , and only on I2C bus.

This driver is based on the https://github.com/winneymj/CircuitPython_SH1106

The previous driver displayed an image with an error where the final pixels were shifted to a new line. Now, Gemini AI has rewritten it so that the error no longer occurs on my display.
I can't assess the validity of the above modification, but I'm posting it here because I haven't found another that works, and it might be useful to someone else.
