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
import threading

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
    return [int(x) for x in line.strip('\r\n').split(' ')]


def log_message(message):
    return [time.time(), message]


def parse_line_generic(line, x, y, log, strip='\r\n'):
    line_stripped = line.strip(strip)
    if line_stripped == '':
        raise ValueError
    try:
        data = [int(i) for i in line_stripped.split(' ')]
        if len(data) == 2:
            if ((data[0] < 2**16) and (data[0] > -2**16) and
               (data[1] < 2**16) and (data[1] > -2**16)):
                x.append(data[0])
                y.append(data[1])
            else:
                log.append(log_message(data))
        else:
            log.append(log_message(data))
        return data
    except ValueError:
        log.append(log_message(line_stripped))
        raise


# def parse_line(line, data, log, stop_message):


class TeensyIO(object):

    messages = ("Teensy reset", "Start acquisition", "Continuing", "Stopped")

    stop_message = "Done"

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


    def run(self, timeout=1):
        """Run data acquisition for a certain length of time."""
        start_time = time.time()
        self.s.write('r')
        self.x = []
        self.y = []
        while time.time() < (start_time + timeout):
            line = self.s.readline().strip('\r\n')
            parse_line_generic(line, self.x, self.y, self.log)

        self.s.write('s')
        for line in self.s.readlines():
            parse_line_generic(line, self.d, self.log)

    def run_and_plot(self, frames=None):
        fig = plt.figure()
        ax = plt.axes(xlim=(-32768, 2**16), ylim=(-32768, 32768))
        line, = ax.plot([], [])


        self.x = []
        self.y = []

        self.s.write('r')

        def init():
            line.set_data([], [], )
            return line,

        left_over = [""]
        def animate(i):
            try:
                bytesToRead = self.s.inWaiting()
                serial_lines = self.s.read(bytesToRead).split('\r\n')
                serial_lines[0] = left_over[0] + serial_lines[0]
                left_over[0] = serial_lines.pop()
                for line_ in serial_lines:
                    try:
                        parse_line_generic(line_, self.x, self.y, self.log)
                    except ValueError:
                        pass
                # I could check for "stop message if necessary."
                print i
            except KeyboardInterrupt:
                self.s.write('s')
                line.set_data(self.x, self.y)
                raise
            
            line.set_data(self.x, self.y)
            return line,

        anim = animation.FuncAnimation(fig, animate, frames=frames, repeat=False, 
                                        init_func=init, interval=100,
                                blit=True)

        plt.show()

        sleep(2)

        plt.close()

        self.s.write('s')

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
    t.run_and_plot()
    t.s.write('s')
    t.save_df('test_plot.csv')

def test():
    test_plot()


# Versioneer versioning
# from ._version import get_versions
# __version__ = get_versions()['version']
# del get_versions