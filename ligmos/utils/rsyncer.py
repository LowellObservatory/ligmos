# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 19 Sep 2018
#
#  @author: rhamilton

"""One line description of module.

Further description.
"""

from __future__ import division, print_function, absolute_import

import subprocess as sub


def subpRsync(src, dest, cmd=None, args=None, timeout=600., debug=True):
    """
    rsync, called via subprocess to get at the binary on the local machine
    """
    if cmd is None:
        cmd = 'rsync'

    if args is None:
        args = ['-arvz', '--progress']

    try:
        subcmdwargs = [cmd] + args + [src, dest]
        # NOTE: subprocess.run() is ONLY in Python >= 3.5! Could rewrite to
        #   use subprocess.Popen, but I find the subprocess.CompletedProcess
        #   instance that run() returns pretty nice.
        output = sub.run(subcmdwargs, timeout=timeout,
                         stdout=sub.PIPE, stderr=sub.PIPE)

        # Check for anything on stdout/stderr
        if debug is True:
            if output.stdout != b'':
                print((output.stdout).decode("utf-8"))

        # If the return code was non-zero, this will raise CalledProcessError
        output.check_returncode()

        # If we're here, then we're fine. Stay golden, Ponyboy
        return 0
    except sub.TimeoutExpired as err:
        errstr = parseRsyncErr(err.stderr)
        if errstr is None:
            errstr = "'%s' took too long!" % (" ".join(err.cmd))
        if debug is True:
            print("Full STDERR: ", end='')
            print((err.stderr).decode("utf-8"))

        errstr = "'%s' timed out" % (" ".join(err.cmd))

        return -99, errstr
    except sub.CalledProcessError as err:
        errstr = parseRsyncErr(err.stderr)
        if errstr is None:
            errstr = "'%s' returned code %d" % (" ".join(err.cmd),
                                                err.returncode)
        if debug is True:
            print("Full STDERR: ", end='')
            print((err.stderr).decode("utf-8"))

        return -999, errstr
    except FileNotFoundError as err:
        if debug is True:
            print("rsync command not found!")
            errstr = err.strerror

        return -9999, errstr


def parseRsyncErr(errbuf):
    """
    """
    # We're in Python 3 territory, so err.stderr is a bytestring!
    if isinstance(errbuf, bytes) is True:
        errstr = errbuf.decode("utf-8")
    elif isinstance(errbuf, str) is True:
        errstr = errbuf
    else:
        errstr = None

    print(errstr)

    errsplit = errstr.split("\n")
    if errsplit[0].lower().startswith("rsync: "):
        errmsg = errsplit[0]
    else:
        errmsg = None

    return errmsg
