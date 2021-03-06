# -*- coding: utf-8 -*-
"""
============================
teensyio
============================
"""
import matplotlib as mpl
mpl.use('Qt4Agg')

import socket
import serial
import io

import matplotlib.pyplot as plt
from matplotlib import animation
import numpy as np
from serial.tools.list_ports import comports
import time
import pandas as pd
from time import sleep

# import bunch

def ls_ports():
    return [x for x in comports()]

def _m():
    """See http://stackoverflow.com/a/22679451/2823213"""

    sock = socket.socket()
    sock.bind(("127.0.0.1",12346))
    sock.listen(3)
    print "Waiting on connection"
    conn = sock.accept()
    print "Client connected"

    while True:
            try:
                m = conn[0].recv(4096)
                conn[0].send(m[::-1])
            except KeyboardInterrupt:
                break

    sock.close()


def find_teensy():
    cu = [port for port in comports()
           if 'cu.usb' in port[0] and 'USB Serial' in port[1]]
    if len(cu) == 1:
        return cu[0][0]
    else:
        raise ValueError("Multiple ports found: {}".format(cu))


def parse_int(line):
    return [int(x) for x in line.strip('\n').split(' ')]


def log_message(message):
    return [time.time(), message]


def parse_line_generic(line, x, y, log, strip='\r\n'):
    line_stripped = line.strip(strip)
    if line_stripped == '':
        return None
    try:
        data = [int(i) for i in line_stripped.split(' ')]
        if len(data) == 2:
            x.append(data[0])
            y.append(data[1])
        else:
            log.append(log_message(data))
        return data
    except ValueError:
        log.append(log_message(line_stripped))
        return None


# def parse_line(line, data, log, stop_message):

def arbitrary_line_split(buf, newline='\n', return_if_empty=False):
    left_over = ""
    while True:
        bytesToRead = buf.inWaiting()
        lines = buf.read(bytesToRead).split(newline)
        lines[0] = left_over + lines[0]
        left_over = lines.pop()
        if return_if_empty:
            if (len(lines) == 0) and (left_over == ''):
                return
        yield lines

# Need a class to represent the circuit state. Current ranges, voltage ranges, etc.

# cs = bunch.Bunch(
#     dac_bit=12,
#     adc_bits=12,
#     self.v_max = 3.3,
#     self.v_min = -3.3,
#     )


class TeensyIO(object):

    messages = ("Teensy reset", "Start acquisition", "Continuing", "Stopped")

    stop_message = "Done"

    current_ranges = {'3uA': 3, '30uA':30, '300uA':300, '3mA':3000}    

    def __init__(self, port, timeout=1, x_name='x', y_name='y',
                                        x_scale=1,  y_scale=1, **kwargs):
        self.s = serial.Serial(port, timeout=timeout, **kwargs)
        self.x_name = x_name
        self.y_name = y_name
        self.x_scale = x_scale
        self.y_scale = y_scale
        self.log = list()

    def __repr__(self):
        return "TeensyIO(port={s.port}, timeout={s.timeout})".format(s=self.s)

    def send_cmd(self, cmd, printing=True):
        self.s.write(cmd)
        lines = self.s.readlines()
        if printing:
            print("".join(lines))

        return lines

    def setup_cyclic_voltamettry(self, V_start=0, V_max=4095,
                                 V_min=0, V_end=0, N_cycles=1, current_range='3mA', printing=True):
        """

        Raises AttributeError if current range incorrect. Possible values:

          3uA
         30uA
        300uA
          3mA
        """
        cr = self.current_ranges[current_range]

        text = "cv set {V_start} {V_max} {V_min} {V_end} {N_cycles} {cr} ".format(
            V_start=V_start, V_max=V_max, V_min=V_min, V_end=V_end,
            N_cycles=N_cycles, cr=cr)

        self.s.write(text)

        self.s.write('print quit ')

        for line in self.s.readlines():
            self.log.append(line)
            if printing:
                print(line.strip('\n'))



    # def setup_cyclic_voltamettry(self, V_start=0, V_max=3.3, V_min=-3.3, V_end=0,
    #     N_cycles=1, printing=True):

    def run(self, timeout=1):
        """Run data acquisition for a certain length of time."""
        start_time = time.time()
        self.s.write('cv run ')
        self.x = []
        self.y = []
        while time.time() < (start_time + timeout):
            line = self.s.readline().strip('\r\n')
            parse_line_generic(line, self.x, self.y, self.log)

        self.s.write('q')
        self.s.write('quit ')
        
        for line in self.s.readlines():
            parse_line_generic(line, self.x, self.y, self.log)



    def run_and_plot(self, xlim=(0, 4095), ylim=(0, 4095), frames=None):
        fig = plt.figure()
        ax = plt.axes(xlim=xlim, ylim=ylim)
        line, = ax.plot([], [])


        self.x = []
        self.y = []

        self.s.write('cv run ')

        gen = arbitrary_line_split(self.s)

        def init():
            line.set_data([], [], )
            return line,

        def animate(i):
            try:
                serial_lines = gen.next()
                for line_ in serial_lines:
                    parse_line_generic(line_, self.x, self.y, self.log)
                # I could check for "stop message if necessary."
                print i
            except KeyboardInterrupt:
                self.s.write('q')
                line.set_data(self.x, self.y)
                raise
            
            line.set_data(self.x, self.y)
            return line,
        
        anim = animation.FuncAnimation(fig, animate, frames=frames, repeat=False, 
                                        init_func=init, interval=50,
                                        blit=True)
        
        plt.show()
        self.s.write('q ')
        self.s.write('quit ')

        lines = self.s.readlines()
        for line in lines:
            parse_line_generic(line, self.x, self.y, self.log)


        self._make_df()

    def _make_df(self):
        self.df = pd.DataFrame()
        self.df[self.x_name] = self.x
        self.df[self.x_name] *= self.x_scale
        self.df[self.y_name] = self.y
        self.df[self.y_name] *= self.y_scale

    def save(self, filename):
        with io.open(filename, 'w') as f:
            f.write(u'x:\n{}\n\ny:\n{}\n\nlog:\n{}'.format(self.x, self.y, self.log))

    def save_df(self, filename):
        self.df.to_csv(filename)



def test_run():
    teensy_port = find_teensy()
    t = TeensyIO(teensy_port)
    t.run()
    print("x size: {}".format(len(t.x)))
    print("y size: {}".format(len(t.y)))
    print("log size: {}".format(len(t.log)))
    print("x tail: \n{}".format(t.x[max(-25, -len(t.d)):]))
    print("y tail: \n{}".format(t.y[max(-25, -len(t.d)):]))
    print("log:\n{}".format(t.log))
    t.save('test_run.log.txt')

def test_plot():
    teensy_port = find_teensy()
    t = TeensyIO(teensy_port, timeout=1, baudrate=115200)
    t.run_and_plot(xlim=(-32768, 2**16), ylim=(-32768, 32768))
    t.s.write('s')
    t.save_df('test_plot.csv')
    t.save('test_plot.log.txt')

def test():
    test_plot()


# Versioneer versioning
# from ._version import get_versions
# __version__ = get_versions()['version']
# del get_versions