# Notes during the creation of this package

- Initial version has an object that can "run" a fake data acquisition
    - `electrochemistry_cli` commit d501aaf061b4fd15fe23c91278c455ff7e168288
    - `teensyio` commit 2e361cdc0ba3f00b0f6bd079fe7660ad08ea4e19

The next step, I think is transferring parameters from Python to the teensy. For example, the first command could choose the experiment, for example, by sending,

- `E-Cyclic_Voltametry`
- `E-Constant_potential`

To do this, I need some code on the teensy to parse `E` prefixed send instructions.

Should I also borrow the `V_max 125`, `V_max?` to query syntax?

Settings could be sent back to the computer before starting the experiment as, `Begin Settings`, `V_start=0`, `V_max=125`, `V_min=-250`, `V_end=0`, `End Settings`.

All of this command line syntax should be bundled up nicely so it doesn't have to be re-written. Should I check the C code for the cheap-stat?

A lot of subtle bugs / serial issues when I tried to send / read data quickly. No issues if I just send / read data slowly, which should be fine for now.

Matplotlib taking up too much time? Still this is functioning for now.

No problems if I use a 50 ms delay between data points. No missed data points. No problems with a 5 ms delay between data points either. With a 0.5 ms delay between data points, there were a few missed data points / broken lines, all of which looked like, `100 100\r\n200 200`.

I rewrote the code getting the data from the serial port as a generator; it seems to work almost perfectly!

Next steps are adding a python method to set up the experiment, and adding code to actually run / simulate the experiment better on the Teensy.

I should also check performance on Windows at some point, and check whether I can run this in an IPython notebook (It will probably / should probably open a new window for this).
