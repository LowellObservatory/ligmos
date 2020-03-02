# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 25 May 2018
#
#  @author: rhamilton

"""workerSetup: Common core for Data Servants

This is for codes which are designed to live on one machine,
and do some actions possibly passing things to other workers.

There can only be one 'procname' instance running on a machine,
controlled via a PID file in /tmp/ as well as some command line options to
kill/restart the process.
"""

from __future__ import division, print_function, absolute_import

import os
import time
import signal

from . import defaultParser
from ..utils import common, logs, pids, confparsers, classes


def toServeMan(procname, conffile, passfile, log,
               extraargs=None,
               conftype=classes.baseTarget,
               logfile=True, enableCheck=True, desc=None):
    """Main entry point, which also handles arguments.

    ... it's - it's a cookbook!

    This will parse the arguments specified in XXXXXXXX

    THIS IS OUT OF DATE! MUCH HAS CHANGED! LIVE IN FEAR!

    Args:
        procname (:obj:`str`)
            Process name to search for another running instance.
        logfile (:obj:`bool`, optional)
            Bool to control whether we write to a logfile (with rotation)
            or just dump everything to STDOUT. Useful for debugging.
            Defaults to True.
        parser (:obj:`function`)
            Parser function that interprets options.
            Should be the reference to the name of the relevant function
            since it's called here.

    Returns:
        idict (:class:`dataservants.utils.common.InstrumentHost`)
            Class containing instrument machine target information
            populated via :func:`dataservants.utils.confparsers.parseInstConf`.
        args (:class:`argparse.Namespace`)
            Class containing parsed arguments, returned from
            :func:`dataservants.iago.parseargs.parseArguments`.
        runner (:class:`dataservants.utils.common.HowtoStopNicely`)
            Class containing logic to catch ``SIGHUP``, ``SIGINT``, and
            ``SIGTERM``.  Note that ``SIGKILL`` is uncatchable.
    """
    # Time to wait after a process is murdered before starting up again.
    #   Might be over-precautionary, but it gives time for the previous process
    #   to write whatever to the log and then close the file nicely.
    killSleep = 30

    # Setup termination signals
    runner = common.HowtoStopNicely()

    # Setup argument parsing *before* logging so help messages go to stdout
    #   NOTE: This function sets up the default values when given no args!
    #
    #   REMOVE SOON.
    #   Also check for kill/fratracide options so we can send SIGTERM to the
    #   other processes before trying to start a new one
    #   (which PidFile would block)
    #   ALSO NOTE: If you give a custom one, it needs (at a minimum):
    #       fratricide|kill, log, nlogs, config, passes
    parser = defaultParser.parseArguments(conf=conffile, passes=passfile,
                                          prog=procname, log=log, descr=desc)

    if extraargs is not None:
        parser = extraargs(parser)

    # Actually parse the things
    args = parser.parse_args()

    # Overly complicated nonsense, will be removed soon.
    #   If we got in here, that means that PidFile's checks already worked
    # pid = pids.check_if_running(pname=procname)

    # # Slightly ugly logic
    # if pid != -1:
    #     if (args.fratricide is True) or (args.kill is True) or\
    #        (args.kill9 is True):
    #         if args.kill9 is False:
    #             print("Sending SIGTERM to %d" % (pid))
    #             try:
    #                 os.kill(pid, signal.SIGTERM)
    #             except Exception as err:
    #                 print("Process not killed; why?")
    #                 # Returning STDOUT and STDERR to the console/whatever
    #                 common.nicerExit(err)
    #         else:
    #             try:
    #                 os.kill(pid, signal.SIGKILL)
    #             except Exception as err:
    #                 print("Process not killed; why?")
    #                 # Returning STDOUT and STDERR to the console/whatever
    #                 common.nicerExit(err)

    #         # If the SIGTERM took, then continue onwards. If we're killing,
    #         #   then we quit immediately. If we're replacing, then continue.
    #         if args.kill is True:
    #             print("Sent SIGTERM to PID %d" % (pid))
    #             # Returning STDOUT and STDERR to the console/whatever
    #             common.nicerExit()
    #         elif args.kill9 is True:
    #             print("Sent SIGKILL to PID %d" % (pid))
    #             # Returning STDOUT and STDERR to the console/whatever
    #             common.nicerExit()
    #         else:
    #             print("LOOK AT ME I'M THE ALIEN COOK NOW")
    #             print("%d sec. pause to allow the other process to exit." %
    #                   (killSleep))
    #             time.sleep(killSleep)
    #     else:
    #         # If we're not killing or replacing, just exit.
    #         #   But return STDOUT and STDERR to be safe
    #         common.nicerExit()
    # else:
    #     if args.kill is True:
    #         print("No %s process to kill!" % (procname))
    #         print("Seach for it manually:")
    #         print("ps -ef | grep -i '%s'" % (procname))
    #         common.nicerExit()

    if logfile is True:
        # Setup logging (optional arguments shown for clarity)
        logs.setup_logging(logName=args.log, nLogs=args.nlogs)

    # Read in the configuration file and act upon it
    idict, cblk = confparsers.parseConfig(args.config, conftype,
                                          passfile=args.passes,
                                          searchCommon=True,
                                          enableCheck=enableCheck,
                                          debug=args.debug)

    return idict, cblk, args, runner
