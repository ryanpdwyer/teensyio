# :title: fabfile.py
# :author: John A. Marohn (jam99@cornell.edu)
# :date: 2014-07-26
# :subject: substitute/extend "make html" and "make open"
# :ref: http://docs.fabfile.org/en/1.4.1/tutorial.html
# :ref: http://ipython.org/ipython-doc/1/interactive/nbconvert.html
from __future__ import (division, print_function,
                        absolute_import, unicode_literals)

import webbrowser
import shutil

import pathlib


# Use subprocess32 if available
try:
    import subprocess32 as subprocess
except:
    import subprocess as subprocess


from invoke import task

cwd = pathlib.Path('.')


def check_output(*args, **kwargs):
    """Subprocess check_output, but prints commands and output by default.
    Also allows printing of error message for helpful debugging.

    Use print_all=False to turn off all printing."""
    print_all = kwargs.pop('print_all', None)
    if print_all is not None:
        print_in = print_all
        print_out = print_all
    else:
        print_in = kwargs.pop('print_in', True)
        print_out = kwargs.pop('print_out', True)

    if print_in:
        print('')
        print(' '.join(args[0]))

    try:
        out_bytes = subprocess.check_output(*args, **kwargs)
        out_lines = out_bytes.decode('utf-8').splitlines()
    except subprocess.CalledProcessError as e:
        # Wrap in try/except so that check_output can print
        raise e

    if print_out:
        for line in out_lines:
            print(line)

    return out_lines


# Helper functions for unix-like removing folders and files.
def rm_rf(*args):
    """Recursively delete directories, if they exist"""
    for directory in args:
        try:
            shutil.rmtree(str(directory))
        except OSError:
            pass


@task(default=True)
def help():
    """Print out a helpful message."""

    print("""\
Usage:  inv[oke] [--core-opts] task1 [--task1-opts] ... taskN [--taskN-opts]

Tasks:

clean      Delete the contents of the _build/ directory
html       Create sphinx documentation as stand-alone HTML files
open       Open the HTML documentation in a web browser


To see more about a specific task, run invoke --help task""")


@task
def clean():
    """Delete the contents of the _build/ directory."""
    rm_rf(cwd/'_build')


@task
def html():
    """Create sphinx documentation as stand-alone HTML files."""
    check_output(['sphinx-build', '-b', 'html', '.', str(cwd/'_build/html')])


@task
def open():
    """Open the HTML documentation in a browser"""
    index_path = cwd/'_build/html/index.html'
    webbrowser.open(index_path.absolute().as_uri())
