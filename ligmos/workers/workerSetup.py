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

from . import defaultParser
from ..utils import common, logs, confparsers, classes


def toServeMan(conffile, passfile, log,
               extraargs=None,
               conftype=classes.baseTarget,
               logfile=True, enableCheck=True, desc=None):
    """Main entry point, which also handles arguments.

    ... it's - it's a cookbook!

    This will parse the arguments specified in XXXXXXXX

    THIS IS OUT OF DATE! MUCH HAS CHANGED! LIVE IN FEAR!

    Args:
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
    # Setup termination signals
    runner = common.HowtoStopNicely()

    # Setup argument parsing *before* logging so help messages go to stdout
    #   NOTE: This function sets up the default values when given no args!
    #
    #   ALSO NOTE: If you give a custom one, it needs (at a minimum):
    #       log, nlogs, config, passes
    parser = defaultParser.parseArguments(conf=conffile, passes=passfile,
                                          log=log, descr=desc)

    if extraargs is not None:
        parser = extraargs(parser)

    # Actually parse the things
    args = parser.parse_args()

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
