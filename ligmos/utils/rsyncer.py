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


def subpRsync(cmd, src, dest, args=None, printErrs=True, timeout=600.):
    """
    rsync, called via subprocess to get at the binary on the local machine
    """
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
        if output.stdout != b'':
            print((output.stdout).decode("utf-8"))

        # If the return code was non-zero, this will raise CalledProcessError
        output.check_returncode()

        # If we're here, then we're fine. Stay golden, Ponyboy
        return 0
    except sub.TimeoutExpired as err:
        if printErrs is True:
            print("Timed out!")
            print("'%s' timed out" % (" ".join(err.cmd)))

        return -99
    except sub.CalledProcessError as err:
        if printErrs is True:
            print("Command error!")
            print("'%s' returned code %d" % (" ".join(err.cmd),
                                             err.returncode))
            # We're in Python 3 territory, so err.stderr is b'' so convert
            print("Standard Error Output:")

            print((err.stderr).decode("utf-8"))

        return -999
    except FileNotFoundError as err:
        if printErrs is True:
            print("Command not found!")
            print(err.strerror)

        return -9999
