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

I have an initializer `serialInitCyclicVoltamettrySettings` which reads values from the serial port and then sets the appropriate value in the cvs structure.

IV Curve
========

The immediate goal is to get a version of the code working to collect and display a current-voltage curve.

Goals:

- Allow current voltage curve to be collected from -3 to +3 volts, using op amps and a 9 V battery to level shift (or start with the Analog Discovery).
- 2x amplifier 0 to 3 V to -3 to 3 V
- Current to voltage converter, initially set such that 10 mA = 3 V
- Max current setting; automatically reserve scan direction or stop?

Let's start without most of these, just 0 to 3 V, with a 10 mA = 3 V current to voltage converting op-amp. The teensy DAC is 12-bit, so we have 0.7 mV per division with a 3 V range, 1.4 mV per division with a 6 V range.

Split supply
============

See http://tangentsoft.net/elec/vgrounds.html for some interesting circuits.

LT
==

LT1461CCS8-3.3 3.3 V voltage reference.

LT application note an16f has some useful information on using the LT1050 as a buffer to decouple the capacitive response of the electrochemical cell.

Switches
========

High quality analog switches are pretty expensive; the lowest noise option is surely a relay. Here are some parts to consider.

CD4041 (basic CMOS part, 150 to 500 ohm on resistance, depending on supply voltage and signal level)

TC4S66F,LF Cheap SPST switch on digikey. Probably the same, roughly, as the CD404.

Coto 9007-05-00, cheap relay, non latching coil (latching coil would be better)

I don't think I need relays, probably, at least not for current ranges down to say, 100 nA full scale. However, low / flat on resistance is important for this application. The ADG451/2 is probably a good option.

The ADG1612 is also a really nice part. Only available in surface mount, but about 1.5 plus or minus 0.2 ohm on resistance, even at ±5 volt supplies.

New Circuit Layout
==================

New circuit layout tries to do a good a job as possible with the parts I currently have on hand. The implementation is still a little unwieldly, 8 op-amps, a difference amplifier, voltage reference, 2 switches, and 2 current buffers.

I'd like to OSHPark a nice implementation of this. Options: Should I use ±5 volt supplies from two batteries? That would let me use the LT1010. 

Digikey
=======

869-1002-ND is a reasonable priced solar cell, which would be fun to test. I can't think of any other really interesting systems, besides other kinds of solar cells. Transistors are interesting in theory, but they require 2 voltage sources, which is pretty annoying.

A good jellybean op-amp for single supply / low voltage work is the TLV272, about a dollar in quantities of 1 to 10.
