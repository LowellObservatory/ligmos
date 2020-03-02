# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on Thu Feb 15 16:58:53 2018
#
#  @author: rhamilton

"""Classes and functions used by any and all servants.
"""

from __future__ import division, print_function, absolute_import

import sys
import time
import signal
import datetime as dt

from . import ssh as mssh
from . import multialarm as malarms


class processDescription():
    """Class to collect function references and associated arguments.

    All attributes can be set during class instantiation and will be
    set to the specified values.  No checks are done for KeyErrors so it'll
    just make attributes all day.

    .. warning::
        ``**kwargs`` sent to processDescription as an argument
        are **different** than ``kwargs`` assigned to the attribute!
        The former allows setting all (and other) attributes of this class;
        the latter allows the sending of specific keyword arguments to
        ``func``!

    Args:
        **kwargs: Arbitrary keyword arguments.

    Attributes:
        func (:obj:`function`)
            Reference to the function that will be called with ``args``
            and ``kwargs`` specified in this class.
        timedelay (:obj:`int`)
            Time to sleep before calling ``func``.
        priority (:obj:`int`)
            Relative priority to assign to ``func`` if using :mod:`sched`.
        args (:obj:`list`)
            Positional arguments to send along to ``func``.
        kwargs (:obj:`dict`)
            Keyword arguments to send along to ``func``.


        THIS NEEDS TO BE UPDATED!!!!!!

    .. image:: https://media.giphy.com/media/12NUbkX6p4xOO4/giphy.gif
    """
    def __init__(self, **kwargs):
        self.func = None
        self.name = ''
        self.maxtime = 60
        self.timedelay = 0.
        self.needSSH = False
        self.args = []
        self.kwargs = {}

        for each in kwargs:
            # print("Setting %s to %s" % (each, kwargs[each]))
            setattr(self, each, kwargs[each])


class HowtoStopNicely():
    """Class to catch signals and trigger the instantiating process to exit.

    Takes no arguments, but contains a few parameters to help pass
    the process information around.

    When ``SIGHUP``, ``SIGINT``, or ``SIGTERM`` is issued,
    :func:`signal_handler` will be called which will set ``halt`` to True.

    .. warning::
        It is the instantiating process' problem to periodically check if
        ``halt`` has been set to True and to act accordingly.

    Attributes:
        pidfile (:obj:`str`)
            String containing the path to the active PID sentinel file.
            Defaults to :obj:`None` and must be set after the class is inited.
        halt (:obj:`bool`)
            Bool representing whether the calling function should stop
            (== True) or continue onwards (== False).

    .. note::
        ``kill PID`` will issue ``SIGTERM``, and this will handle it
        gracefully so a clean start is possible.

        ``kill -9`` will issue ``SIGKILL`` and can never be caught.
        The logic in :func:`dataservants.utils.pids.check_if_running`
        should let the process start again, though.
    """
    def __init__(self):
        # Set up signal handling before anything else!
        self.pidfile = None
        self.halt = False
        signal.signal(signal.SIGHUP, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Actions to take after a signal is caught.

        Sets the ``halt`` attribute to True, allowing the calling function
        to know that someone wants it to stop.

        Args:
            signum (:obj:`int`)
                A signal number indicating which signal was recieved.
                See :obj:`signal` for details or in a terminal look
                at the output of ``kill -l``.
            frame (:obj:`frame`)
                Stack frame of where the interrupt occured.
        """
        # Python3's signal module is way nicer...
        try:
            print("Got %s; stopping..." % (signal.Signals(signum).name))
        except AttributeError:
            # Shouldn't ever really get here, but I'll handle it anyways
            print("Got signal num. %s; stopping..." % (signum))

        self.halt = True


def nicerExit(err=None):
    """Signal handling function to reset any logging and then exit.

    Assuming logging is set up, this handler will reset :obj:`sys.stdout` and
    :obj:`sys.stderr` back to their original values to allow output to the
    console rather then hidden away in a log.

    If ``err`` is specified then print that to the log, **then** reset
    :obj:`sys.stdout` and :mod:`obj.stderr`.

    Args:
        err (:obj:`Exception` or :obj:`str`)
            Could be either data type, depending on how it is called.
            Defaults to None, indicating a clean exit.  If it is not None,
            then :func:`sys.exit` will be called with ``-1`` and a traceback
            might ensue, depending on your settings.
    """
    cond = 0
    if err is not None:
        print("FATAL ERROR: %s" % (str(err)))
        cond = -1

    # Returning STDOUT and STDERR to the console/whatever
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

    sys.exit(cond)


def printPreamble(p, idict):
    # Helps to put context on when things are stopped/started/restarted
    print("Current PID: %d" % (p.pid))
    print("PID %d recorded at %s now starting..." % (p.pid, p.filename))

    # Preamble/contextual messages before we really start
    print("Beginning to monitor the following hosts:")
    print("%s\n" % (' '.join(idict.keys())))
    print("Starting the infinite loop.")
    print("Kill PID %d to stop it." % (p.pid))


def instAction(each, outertime=None):
    """
    """
    ans = None
    estop = False
    try:
        with malarms.Timeout(id_=each.name, seconds=each.maxtime):
            astart = dt.datetime.utcnow()
            ans = each.func(*each.args,
                            **each.kwargs)
            # print(ans)
    except malarms.TimeoutError as e:
        # SHOULD put this on STDERR so Wadsworth can catch it and see...
        print("Raised TimeOut for " + e.id_)
        print(e)
        # Need a little extra care here since
        #   TimeOutError could be from InstLoop
        #   *or* each.func, so if we got the
        #   InstLoop exception, break out
        if e.id_ == "InstLoop":
            estop = True
        # print(ans)
    finally:
        rnow = dt.datetime.utcnow()
        print("Done with action, %f since start" %
              ((rnow - astart).total_seconds()))
        if outertime is not None:
            rnow = dt.datetime.utcnow()
            print("%f since outer loop start" %
                  ((rnow - outertime).total_seconds()))

    return ans, estop


def instLooper(idict, runner, args, actions, updateArguments, baseYcmd,
               db=None, alarmtime=600):
    """
    Could bump the instrument loop out and back to the main calling function
    if we want to do stuff per-instrument rather than on all the instruments'
    results.
    """
    for inst in idict:
        iobj = idict[inst]

        if db is not None:
            # Get the correct database object for this particular inst
            try:
                dbtab = iobj.database
                dbObj = db[dbtab]
            except AttributeError:
                print("Database tag not found for section %s!" % (inst))
                dbObj = None
            except KeyError:
                print("Database tag %s not specified!" % (dbtab))
                dbObj = None

        # Update all function arguments with new iobj
        cactions = updateArguments(actions, iobj, args, baseYcmd, db=dbObj)

        # Pre-fill our expected answers so we can see fails
        allanswers = [None]*len(cactions)

        if args.debug is True:
            print("\n%s" % ("=" * 11))
            print("Instrument: %s" % (inst))
        try:
            # Arm an alarm that will stop this inner section
            #   in case one instrument starts to hog the show
            startt = dt.datetime.utcnow()

            with malarms.Timeout(id_='InstLoop',
                                 seconds=alarmtime):
                # This will run through each action in turn
                for i, each in enumerate(cactions):
                    # If we need SSH, it's always the first
                    #   positional argument so add it
                    if each.needSSH is True:
                        # Open the SSH connection; SSHHandler
                        #   does all the hard stuff.
                        eSSH = mssh.SSHWrapper(host=iobj.host,
                                               port=iobj.port,
                                               username=iobj.user,
                                               timeout=60,
                                               password=iobj.password,
                                               connectOnInit=True)
                        each.args = [eSSH] + each.args
                    else:
                        eSSH = None

                    if args.debug is True:
                        print("Calling %s" % (str(each.func)))

                    # Perform the action
                    ans, estop = instAction(each, outertime=startt)
                    print("ans:", ans)
                    print("estop:", estop)

                    # If it actually worked, close the connection
                    if eSSH is not None:
                        eSSH.closeConnection()

                    # Save the result if there was one
                    allanswers[i] = ans

                    # Check to see if the action caught
                    #  a timeout intended for the whole
                    #  instrument actionset or just itself
                    if estop is True or runner.halt is True:
                        break
                    else:
                        time.sleep(each.timedelay)

            # Check to see if someone asked us to quit
            if runner.halt is True:
                print("Quit inner instrument loop")
                break
            else:
                # Time to sleep between instruments
                print("Sleeping between instruments")
                time.sleep(5)
        except malarms.TimeoutError as err:
            print(str(err))
            print("%s took too long! Moving on." % (inst))

    return allanswers
