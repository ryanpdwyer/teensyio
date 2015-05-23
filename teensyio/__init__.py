# -*- coding: utf-8 -*-
"""
============================
teensyio
============================
"""


import socket
import serial
import io
from serial.tools.list_ports import comports
import time
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

def log_message(message, strip='\r\n'):
    return [time.time(), message.strip(strip)]

def parse_line_generic(line, data, log, strip='\r\n'):
    line_stripped = line.strip(strip)
    if line_stripped == '':
        return 1
    try:
        x = [int(x) for x in line_stripped.split(' ')]
        data.append(x)
    except ValueError:
        log.append(log_message(line_stripped))

    return 0


# def parse_line(line, data, log, stop_message):


class TeensyIO(object):

    messages = ("Teensy reset", "Start acquisition", "Continuing", "Stopped")

    stop_message = "Done"

    def __init__(self, port, timeout=1, **kwargs):
        self.s = serial.Serial(port, timeout=timeout, **kwargs)

        self.log = list()

    def __repr__(self):
        return "TeensyIO(port={s.port}, timeout={s.timeout})".format(s=self.s)


    def run(self, timeout=1):
        """Run data acquisition for a certain length of time."""
        start_time = time.time()
        self.s.write('r')
        self.d = []
        while time.time() < (start_time + timeout):
            line = self.s.readline().strip('\r\n')
            parse_line_generic(line, self.d, self.log)

        self.s.write('s')
        for line in self.s.readlines():
            parse_line_generic(line, self.d, self.log)

    def save(self, filename):
        with io.open(filename, 'w') as f:
            f.write(u'data:\n{}\n\nlog:\n{}'.format(self.d, self.log))




def test_run():
    teensy_port = find_teensy()
    t = TeensyIO(teensy_port)
    t.run()
    print("data size: {}".format(len(t.d)))
    print("log size: {}".format(len(t.log)))
    print("data tail: \n{}".format(t.d[max(-25, -len(t.d)):]))
    print("log:\n{}".format(t.log))
    t.save('test_run.log.txt')

def test():
    test_run()

# Versioneer versioning
# from ._version import get_versions
# __version__ = get_versions()['version']
# del get_versions