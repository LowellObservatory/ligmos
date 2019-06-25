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


class Webcam(object):
    """
    Class to contain all the important bits of webcam connection information
    """
    def __init__(self):
        self.type = None
        self.url = None
        self.user = None
        self.password = None
        self.fmas = None
        self.auth = None
        self.odir = None
        self.oname = None
        self.enabled = False


class sneakyTarget(object):
    """
    Subclasses ... nothing!  Mostly a standalone affair.
    """
    def __init__(self):
        self.name = None
        self.broker = None
        self.pubtopic = None
        self.resourcemethod = None
        self.resourcelocation = None
        self.resourceport = None
        self.user = None
        self.password = None
        self.enabled = False


class databaseQuery(object):
    """
    Subclasses...nothing! It's mostly standalone, though it's intended that
    an instance describing the database connection gets shoved into
    self.connection after this is created.

    This isn't intended to be for writing to a database.
    """
    def __init__(self):
        self.database = None
        self.tablename = None
        self.fields = None
        self.fieldlabels = None
        self.tagnames = None
        self.tagvals = None
        self.rangehours = 24


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
        self.password = None
        self.type = None
        self.enabled = False


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

        self.broker = None
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
        self.database = None
        self.databasetable = None

        # Is this legit? Should one delete attributes inherited from a base
        #   that you actually don't really need?  Who knows!
        delattr(self, 'type')
        delattr(self, 'name')
