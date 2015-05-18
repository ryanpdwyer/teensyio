# Invoke tasks file
# Python 2/3 Makefile replacement
# To do:
#   - Add commands to build docs
# Dependencies:
# six, packaging, pathlib, invoke
# Python2 (optional): subprocess32
from __future__ import (division, print_function,
                        absolute_import, unicode_literals)
import os
import shutil
import platform

import pathlib
import packaging.version
from six.moves import input
from invoke import task

# Use subprocess32 if available
try:
    import subprocess32 as subprocess
except:
    import subprocess as subprocess


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


windows = platform.system() == 'Windows'


def find_git_cmd(windows):
    """Determine whether the git command is git or git.cmd on Windows.
    This changed in version 1.8.3"""
    git = 'git'

    if windows:
        try:
            check_output([git, '--version'])
        except subprocess.CalledProcessError:
            try:
                git = 'git.cmd'
                check_output([git, '--version'])
            except subprocess.CalledProcessError:
                msg = "git does not appear to be on your path."
                raise subprocess.CalledProcessError(msg)

    return git

git = find_git_cmd(windows)


# Helper functions for unix-like removing folders and files.
def rm_rf(*args):
    """Recursively delete directories, if they exist"""
    for directory in args:
        try:
            shutil.rmtree(str(directory))
        except OSError:
            pass


def rm(*args):
    """Delete all files provided"""
    for path in args:
        try:
            os.remove(str(args))
        except OSError:
            pass


# Helper functions for getting version numbers
def git_describe():
    result = check_output(['git', 'describe', '--tags', '--dirty', '--always'])
    return result.stdout


def version():
    result = check_output(['python', 'setup.py', '--version'])
    return result.stdout


@task(default=True)
def help():
    print("""
Usage:  inv[oke] [--core-opts] task1 [--task1-opts] ... taskN [--taskN-opts]

Tasks:

docs            build the docs and open in a webbrowser
build_docs      build the docs
clean           Remove compiled python files, build directories
test            Run tests for package (python setup.py test)
release         Upload to PyPI after running tests and checking version number

To see more about a specific task, run invoke --help task""")


@task
def docs():
    """Use the docs subdirectory tasks.py to build and open docs."""
    os.chdir('docs')
    check_output(['invoke', 'html', 'open'])


@task
def build_docs():
    """Just build the docs using Sphinx, don't open in a browser"""
    os.chdir('docs')
    check_output(['invoke', 'html'])


@task
def clean():
    """Remove build directories, compiled python files"""
    rm_rf('dist')
    rm(*cwd.rglob("*.py[cod]"))

    rm_rf('build', '__pycache__')

    rm_rf(*cwd.glob('*.egg'))


@task
def test():
    """Test the package using python setup.py test"""
    check_output(['python', 'setup.py', 'test'])


@task
def check_version():
    """Raise an error if the version number is not PEP440 compatible"""
    packaging.version.Version(version())
    print("Version okay.")


@task
def check_version_tag():
    """Before releasing, check that the version matches the git tag"""
    git_describe_version = git_describe()
    setuppy_version = version()
    if setuppy_version == git_describe_version:
        print("Versions match.")
    elif 'dirty' in git_describe_version:
        raise ValueError("""Working directory has uncommited changes.\
            Commit before releasing.""")
    else:
        choice = input("Release without tagging\n(version {0})? [y/N]\n".format(
            setuppy_version)).lower()
        if choice[0] == 'y':
            print("Continuing")
        else:
            raise ValueError("Stopping.")


@task(clean, test, check_version, check_version_tag)
def release():
    """Check that tests pass, the version is correct, then build source, wheel
    distributions, upload to PyPI using twine."""
    check_output(['python', 'setup.py', 'sdist', 'bdist_wheel'])
    check_output(['twine', 'upload', 'dist/*'])
