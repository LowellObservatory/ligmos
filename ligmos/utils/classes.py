# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 7 Jun 2019
#
#  @author: rhamilton

"""
"""

from __future__ import division, print_function, absolute_import

from .common import nicerExit


class baseTarget(object):
    """
    Empty class that gets inherited by basically everything since it contains
    most/all the usual stuff you'd need to connect to a ... thing.
    """
    def __init__(self):
        self.name = None
        self.host = None
        self.port = 22
        self.user = None
        self.pasw = None
        self.type = None
        self.enabled = False


class databaseQuery(object):
    """
    Subclasses...nothing! It's mostly standalone, though it's intended that
    an instance describing the database connection gets shoved into
    self.hookup here for actual usage.

    Can be used to query or write to a database...?
    """
    def __init__(self):
        self.hookup = None
        self.dbname = None
        self.tablename = None
        self.fields = None
        self.tagnanes = None
        self.tagvals = None
        self.rangehours = 24


class brokerCommandingTarget(baseTarget):
    """
    Subclasses baseTarget class
    """
    def __init__(self):
        # Gather up the properties from the base class
        super().__init__()

        self.cmdtopic = None
        self.replytopic = None


class snoopTarget(baseTarget):
    """
    Subclasses baseTarget class
    """
    def __init__(self):
        # Gather up the properties from the base class
        super().__init__()

        self.topics = None


class deviceTarget(baseTarget):
    """
    Subclasses baseTarget class
    """
    def __init__(self):
        # Gather up the properties from the base class
        super().__init__()

        # All of the devices will be parsed and put into this list, so
        #   you can figure out how many there are just by len(devices).
        self.devices = None


class instrumentDeviceTarget(baseTarget):
    """
    Subclasses baseTarget class
    """
    def __init__(self):
        # Gather up the properties from the base class
        super().__init__()

        self.tag = None
        self.type = None
        self.serialURL = None
        self.brokertopic = None


class dataTarget(baseTarget):
    """
    Subclasses baseTarget class
    """
    def __init__(self):
        # Gather up the properties from the base class
        super().__init__()

        self.srcdir = None
        self.dirmask = None
        self.filemask = None
        self.destdir = None
        self.engEnabled = False

        # These are updated/used elsewhere functionally
        self.running = False
        self.timeout = 60


class hostTarget(baseTarget):
    """
    Subclasses baseTarget class

    Primarily for Alfred the DataServant, who looks after instrument
    host machines.

    srcdir: directory in which to measure free space, specified so we
            get the most relevant mount point assuming the machine has many

    procmon: process to look for and monitor; passed to Yvette, and used in
             psutil to search for processes matching that name
    """
    def __init__(self):
        # Gather up the properties from the base class
        super().__init__()

        self.srcdir = None
        self.procmon = None


def addPass(base, password=None, debug=False):
    """Add in password information from a separate file for ``user``.

    This small function allows the breaking up of usernames from passwords
    into separate .conf files, mainly for a little extra security when
    posting this all to GitHub.

    .. seealso::
        ``passwords.conf-TEMPLATE`` in the examples directory.

    Args:
        password (conf (:class:`configparser.ConfigParser`, optional)
            Configuration information parsed from a .conf file.
            Defaults to None.  If password is not None, then a
            ``password`` attribute is created if matching usernames
            are found.
    debug (:obj:`bool`, optional)
        Bool to trigger additional debugging outputs. Defaults to False.
    """
    if password is None:
        if debug is True:
            print("Password is empty!!")
    else:
        setattr(base, 'pasw', password)

    return base
