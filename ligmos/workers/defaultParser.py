# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 10 Aug 2018
#
#  @author: rhamilton

"""One line description of module.

Further description.
"""

from __future__ import division, print_function, absolute_import

import argparse as argp


def parseArguments(conf=None, prog=None, passes=None, log=None, descr=None):
    """Setup command line arguments that everyone will use.
    """
    fclass = argp.ArgumentDefaultsHelpFormatter

    if descr is None:
        description = "ADataServant: Doing Things That Are Helpful"
    else:
        description = descr

    parser = argp.ArgumentParser(description=description,
                                 formatter_class=fclass,
                                 prog=prog)

    if conf is None:
        parser.add_argument('-c', '--config', metavar='/path/to/file.conf',
                            type=str,
                            help='File for configuration information',
                            default='./programname.conf', nargs='?')
    else:
        parser.add_argument('-c', '--config', metavar='/path/to/file.conf',
                            type=str,
                            help='File for configuration information',
                            default=conf, nargs='?')

    if passes is not None:
        parser.add_argument('-p', '--passes', metavar='/path/to/file.conf',
                            type=str,
                            help='File for instrument password information',
                            default='./passwords.conf', nargs='?')

    if log is None:
        parser.add_argument('-l', '--log', metavar='/path/to/file.log',
                            type=str,
                            help='File for logging of messages',
                            default='/tmp/programname.log', nargs='?')
    else:
        parser.add_argument('-l', '--log', metavar='/path/to/file.log',
                            type=str,
                            help='File for logging of messages',
                            default=log, nargs='?')

    parser.add_argument('-k', '--kill', action='store_true',
                        help='Kill an already running instance',
                        default=False)

    parser.add_argument('-k9', '--kill9', action='store_true',
                        help='Kill -9 an already running instance',
                        default=False)

    # Note: Need to specify dest= here since there are multiple long options
    #   (and I prefer the fun option name in the code)
    lhtext = 'Kill another instance, then take its place'
    parser.add_argument('-r', '--restart', '--fratricide', action='store_true',
                        help=lhtext, dest='fratricide',
                        default=False)

    parser.add_argument('-n', '--nlogs', type=int,
                        help='Number of previous logs to keep after rotation',
                        default=30, nargs=1)

    parser.add_argument('--debug', action='store_true',
                        help='Print extra debugging messages while running',
                        default=False)

    return parser