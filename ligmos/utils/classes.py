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


class deviceType():
    """
    """
    def __init__(self):
        self.hostname = None
        self.port = None
        self.type = None
        self.tag = None
        self.serialURL = None


class commonParams():
    """
    """
    def __init__(self):
        self.brokertype = ''
        self.brokerhost = ''
        self.brokerport = None
        self.brokeruser = ''
        self.dbtype = None
        self.dbhost = None
        self.dbport = None
        self.dbuser = ''
        self.dbname = ''

    def assignConf(self, conf, ctype):
        """
        A bit shoddy, but it works.  Alternative is to have separate classes
        for database, broker, etc. and use the usual assignConf routine.
        """
        if ctype.lower() == 'broker':
            akeys = ['brokertype', 'brokerhost', 'brokerport', 'brokeruser']
        elif ctype.lower() == 'database':
            akeys = ['dbtype', 'dbhost', 'dbport', 'dbuser', 'dbname']
        else:
            akeys = []

        # This will loop over all the properties defined above!
        for key in akeys:
            try:
                if key.lower() == 'dbtype':
                    if conf[key].lower() == 'none':
                        # SPECIAL handling to capture "None" -> None
                        setattr(self, key, None)
                    else:
                        setattr(self, key, conf[key])
                else:
                    setattr(self, key, conf[key])
            except KeyError as err:
                nicerExit(err)


class baseTarget(object):
    """
    Empty class that gets inherited by everyone needing to add a password
    associated with the host parameter or needing to add in a common block.
    """
    def __init__(self):
        self.name = ''
        self.host = ''
        self.port = 22
        self.user = ''
        self.enabled = False


class brokerCommandingTarget(baseTarget):
    """
    Subclasses baseTarget class
    """
    def __init__(self):
        # Gather up the properties from the base class
        super().__init__()

        self.cmdtopic = ''
        self.replytopic = ''


class snoopTarget(baseTarget):
    """
    Subclasses baseTarget class
    """
    def __init__(self):
        # Gather up the properties from the base class
        super().__init__()

        self.topics = []


class deviceTarget(baseTarget):
    """
    Subclasses baseTarget class
    """
    def __init__(self):
        # Gather up the properties from the base class
        super().__init__()

        # All of the devices will be parsed and put into this list, so
        #   you can figure out how many there are just by len(devices).
        self.devices = []


class dataTarget(baseTarget):
    """
    Subclasses baseTarget class
    """
    def __init__(self):
        # Gather up the properties from the base class
        super().__init__()

        self.srcdir = ''
        self.dirmask = ''
        self.filemask = ''
        self.destdir = ''
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

        self.srcdir = ''
        self.procmon = ''


def addCommonBlock(base, common=None):
    if common is not None:
        base.common = common
    else:
        base.common = None

    return base


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
        base.passw = password

    return base
