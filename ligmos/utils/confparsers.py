# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on Tue Feb 27 12:46:30 2018
#
#  @author: rhamilton

"""Module for configuration and password file parsing.
Meta-functions that use the outputs of these can be found in confutils.
"""

from __future__ import division, print_function, absolute_import

import configparser as conf

from . import classes
from . import confutils


def rawParser(confname):
    """
    A simple minded parsing of the given confname file.
    Returns a configparser object.
    """
    config = None
    try:
        config = conf.SafeConfigParser()
        config.read_file(open(confname, 'r'))
    except IOError as err:
        print("ERROR: Configuration file %s not found!" % (confname))
        print(str(err))

    return config


def parseConfig(conffile, confclass, passfile=None, debug=True,
                searchCommon=True, enableCheck=True):
    """
    Parse the given .conf file.

    if confclass is not None, the sections in conffile are attempted to
    be put into the class referenced by confclass.  Note that this
    should be a reference and *NOT* an instance.

    If searchCommon is true, it attempts to look for 'database-' or 'broker-'
    (or possibly other) tagged sections and assigns them to a
    classes.baseTarget instance named 'comcfg' and if false, 'comcfg' is
    set to None.

    If enableCheck is true, it attempts to look at each (non-common) section
    for the given 'enableKey' and if it's found, and is True, it's added to
    a dict of sections organized by section title and returned.  If it's not
    found, the section is assumed to be DISabled and not added to the returned
    dict.  If enableCheck is False, all sections are returned as a dict.

    Returns a dict of sections and None OR a classes.commonParams instance.
    """
    config = rawParser(conffile)

    if config is None:
        # This now becomes the caller's problem to catch!
        return None, None

    if passfile is not None:
        passwords = rawParser(passfile)
        if passwords is None:
            # Again, make it the caller's problem to watch/fix.
            return None, None
        else:
            # Search for commonality between the password and config
            #   sections, and add passwords where they match
            config = confutils.assignPasses(config, passwords)

    # Order of operations is important!
    #   By checking the enabled status here, we can check to see if the
    #   common database- or broker- sections are enabled/disabled too.
    if enableCheck is True:
        enconfig = checkEnabled(config, enableKey='enabled')
    else:
        enconfig = dict(config)

    comcfg = None
    if searchCommon is True:
        # We pop the common config section if it's found, so need to remember
        #   to get the config back as a return value
        ncconfig, comcfg = checkCommon(enconfig)
    else:
        ncconfig = dict(enconfig)

    # We do the debug output here because it's easier to just work on
    #   all the given dicts rather than dance around the objects
    if debug is True:
        # Just for nice output lines
        sections = config.sections()
        tsections = ' '.join(sections)

        print("Found the following sections in the configuration file:")
        print("%s\n" % tsections)

        if enableCheck is True:
            print("Enabled:")
            esections = ' '.join(enconfig.keys())
            print("%s\n" % esections)

        if searchCommon is True:
            print("Common:")
            bsections = ' '.join(comcfg.keys())
            print("%s\n" % bsections)

    # Now make the config into a proper class of type confclass
    finconfig = {}
    for each in ncconfig:
        classed = confutils.assignConf(ncconfig[each], confclass, debug=debug)
        finconfig.update({each: classed})

    return finconfig, comcfg


def checkCommon(cfg, objtype=None):
    """
    Expects that cfg is a dict of configparser sections, which are then
    assigned to an instance of type objtype.
    """
    comms = {}

    if objtype is None:
        objtype = classes.baseTarget

    # Things that will trigger us
    #   We keep the delimiter separate from the tags because it's easier
    #   to assemble the returned dictionary that way!
    commonTags = ['database-', 'broker-']

    # First get the list of all sections
    sects = cfg.keys()

    for tag in commonTags:
        # See if any start with our current tag, and if so, grab their names
        csecs = [s for s in sects if s.lower().startswith(tag)]

        for each in csecs:
            # Use it to fill the common/core data structure. Since it's a
            #   class method it'll just fill up the class appropriately.
            targObj = confutils.assignConf(cfg[each], objtype)

            # Now purge the common section out so it doesn't get confused
            cfg.remove_section(each)

            # Now add it to our returned dictionary
            comms.update({each: targObj})

    return cfg, comms


def checkEnabled(conf, enableKey='enabled'):
    """
    Expects that conf is still a configparser instance.

    Check the conf for sections with a paramater matching the 'enableKey'
    parameter and return that section IFF (if and only if) it is True.

    If the 'enableKey' is not found, it's assumed to be a disabled section
    and it is NOT returned.
    """
    enset = {}
    for sect in conf.sections():
        en = False
        for key in conf[sect].keys():
            if key.lower() == enableKey.lower():
                en = conf[sect].getboolean(key)
                if en is True:
                    enset.update({sect: conf[sect]})

    return enset
