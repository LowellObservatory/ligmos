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
from ..workers import confUtils as confutils


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
        # If enableCheck was false, there's a DEFAULT section still lingering
        #   about and I hate it.  Check for that and skip it explicitly.
        if each.lower() != 'default':
            classed = confutils.assignConf(ncconfig[each], confclass,
                                           debug=debug)
            finconfig.update({each: classed})

    return finconfig, comcfg


def checkCommon(cfg):
    """
    Expects that cfg is a dict of configparser sections, which are then
    assigned to an instance of an appropriate type for that section.

    database- and broker- are of type classes.baseTarget
    queue is of type classes.brokerCommandingTarget
    """
    comms = {}

    # Things that will trigger us
    #   We keep the delimiter separate from the tags because it's easier
    #   to assemble the returned dictionary that way!
    commonTags = ['database-', 'broker-', 'queue-', 'online-']

    # First get the list of all sections
    sects = cfg.keys()

    for tag in commonTags:
        if tag in ['database-', 'broker-']:
            objtype = classes.baseTarget
        elif tag in ['queue-']:
            objtype = classes.brokerCommandingTarget
        elif tag in ['online-']:
            objtype = classes.onlineTarget

        # See if any start with our current tag, and if so, grab their names
        csecs = [s for s in sects if s.lower().startswith(tag)]

        for each in csecs:
            # Use it to fill the common/core data structure. Since it's a
            #   class method it'll just fill up the class appropriately.
            targObj = confutils.assignConf(cfg[each], objtype)

            # Now purge the common section out so it doesn't get confused
            cfg.pop(each)

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
        try:
            en = conf[sect].getboolean(enableKey)
            if en is True:
                enset.update({sect: conf[sect]})
        except KeyError:
            pass

    return enset


def getterMcGetterface(obj, key, lower=True):
    try:
        kval = getattr(obj, key)
        if lower is True:
            kval = kval.lower()
    except AttributeError:
        kval = None

    return kval


def regroupConfig(config, groupKey='instrument', ekeys=None, delim="_"):
    """
    Reorganize the given (parsed) configuration to be a dict organized by
    the given groupKey.

    If ekeys is not None, and if [hasattr(config[csect], key) for key in ekeys]
    is True, they will be appended (in order, delimited by '_') onto the
    groupKey to form the final grouping key in the returned dict.
    """
    # Reorganize the configuration to be per-instrument
    perInst = {}
    for csect in config:
        inst = getterMcGetterface(config[csect], groupKey)
        if inst is not None and ekeys is not None:
            if isinstance(ekeys, list):
                keytags = None
                for key in ekeys:
                    exval = getterMcGetterface(config[csect], key)
                    if exval is not None:
                        if keytags is None:
                            keytags = exval
                        else:
                            keytags = "%s%s%s" % (keytags, delim, exval)
            else:
                # Default/fallback in case we didn't have any extra tags
                keytags = inst

        if inst is not None:
            # Does this instrument already exist in our final dict?
            #   If so, grab all of the defined devices so far
            if inst in perInst.keys():
                iDevices = perInst[inst]
            else:
                iDevices = {}

            iDevices.update({keytags: config[csect]})
            perInst.update({inst: iDevices})

    return perInst
