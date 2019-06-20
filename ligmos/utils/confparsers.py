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

from . import common
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


def parseConfig(confname, passname=None, debug=True,
                searchCommon=True, enableCheck=True):
    """
    Parse the given .conf file.

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
    config = rawParser(confname)

    if config is None:
        # This now becomes the caller's problem to catch!
        return None, None

    if passname is not None:
        passwords = rawParser(passname)
        if passwords is None:
            # Again, make it the caller's problem to watch/fix.
            return None, None

    comcfg = None
    if searchCommon is True:
        # We pop the common config section if it's found, so need to remember
        #   to get the config back as a return value
        config, comcfg = checkCommon(config)

    if enableCheck is True:
        retconfig = checkEnabled(config, enableKey='enabled')
    else:
        retconfig = dict(config)

    if debug is True:
        # Just for nice output lines
        sections = config.sections()
        tsections = ' '.join(sections)

        print("Found the following sections in the configuration file:")
        print("%s\n" % tsections)

        if searchCommon is True:
            print("Common:")
            bsections = ' '.join(comcfg.keys())
            print("%s\n" % bsections)

        if enableCheck is True:
            print("Enabled:")
            esections = ' '.join(retconfig.keys())
            print("%s\n" % esections)

    return retconfig, comcfg


def parsePassFile(filename, idict, cblk=None, debug=False):
    """
    """
    try:
        config = conf.SafeConfigParser()
        config.read_file(open(filename, 'r'))
    except IOError as err:
        print("WARNING: %s not found! Ignoring it and continuing..." %
              (filename))
        print(str(err))
        return idict

    for each in idict.keys():
        # Get the username for this instrument
        iuser = idict[each].user
        # Now see if we have a password for this username
        if iuser != '':
            try:
                passw = config[iuser]['pw']
            except KeyError:
                if debug is True:
                    print("Username %s has no password!" % (iuser))
                passw = None

            idict[each] = classes.addPass(idict[each], passw)

    # Since we're in here, check the possible 'common' stuff too.
    #  TODO: Clean this up. It's pretty damn sloppy, since None is
    #  getting in here as 'None' (i.e. not the right type)
    if cblk is not None:
        try:
            bpw = config['common-broker']['pw']
            setattr(cblk, 'brokerpass', bpw)
        except KeyError:
            setattr(cblk, 'brokerpass', None)
        try:
            dpw = config['common-database']['pw']
            setattr(cblk, 'dbpass', dpw)
        except KeyError:
            setattr(cblk, 'dbpass', None)

    return idict, cblk


def checkCommon(cfg):
    """
    """
    comms = {}

    # Things that will trigger us
    #   We keep the delimiter separate from the tags because it's easier
    #   to assemble the returned dictionary that way!
    commonTags = ['database-', 'broker-']

    # First get the list of all sections
    sects = cfg.sections()

    for tag in commonTags:
        # See if any start with our current tag, and if so, grab their names
        csecs = [s for s in sects if s.lower().startswith(tag)]

        for each in csecs:
            # Use it to fill the common/core data structure. Since it's a
            #   class method it'll just fill up the class appropriately.
            targObj = classes.baseTarget()
            targObj = confutils.assignConf(targObj, cfg[each])

            # Now purge the common section out so it doesn't get confused
            cfg.remove_section(each)

            # Now add it to our returned dictionary
            comms.update({each: targObj})

    return cfg, comms


def checkEnabled(conf, enableKey='enabled'):
    """
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
