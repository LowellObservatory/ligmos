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
from . import classes as comclass


def parseConfFile(filename, debug=False, abort=True,
                  commonBlocks=True, enableCheck=True):
    """
    Parse the given .conf file.

    If abort is True, than an IOError on the configuration file
    will sink the code and stop immediately. False will return None.

    If commonBlocks is true, it attempts to look for 'common-' tagged sections
    and assigns them to a classes.commonParams instance named 'comcfg' and if
    false, 'comcfg' is set to None.

    If enableCheck is true, it attempts to look at each (non-common) section
    for the given 'enableKey' and if it's found, and is True, it's added to
    a dict of sections organized by section title and returned.  If it's not
    found, the section is assumed to be DISabled and not added to the returned
    dict.  If enableCheck is False, all sections are returned as a dict.

    Returns a dict of sections and None OR a classes.commonParams instance.
    """
    try:
        config = conf.SafeConfigParser()
        config.read_file(open(filename, 'r'))
    except IOError as err:
        if abort is True:
            common.nicerExit(err)
        else:
            print("WARNING: %s not found! Ignoring it and continuing..." %
                  (filename))
            return None, None

    comcfg = None
    if commonBlocks is True:
        # Set up the final resting place for the common database/broker params
        comcfg = comclass.commonParams()

        # We pop the common config section if it's found, so need to remember
        #   to get the config back as a return value
        config, comcfg, df = checkCommon(config, comcfg, blktype='database')
        config, comcfg, bf = checkCommon(config, comcfg, blktype='broker')

        if df is False and bf is False:
            # This means that even though we tried, we didn't find any
            #   common block configurations.
            comcfg = None

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

        if commonBlocks is True:
            print("Common:")
            cblks = []
            if df is True:
                cblks.append("database")
            if bf is True:
                cblks.append("broker")
            bsections = ' '.join(cblks)
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

            idict[each] = comclass.addPass(idict[each], passw)

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


def checkCommon(config, commconfig, blktype='broker'):
    """
    """
    found = False
    if blktype == 'database':
        try:
            # Do we have a database config?
            csec = config['common-database']

            # Use it to fill the common/core data structure. Since it's a
            #   class method it'll just fill up the class appropriately.
            commconfig.assignConf(csec, blktype)

            # Now purge the common section out so it doesn't get confused
            config.remove_section('common-database')
            print("Found common database configuration parameters")
            found = True
        except KeyError:
            pass
    elif blktype == 'broker':
        # Second verse, same as the first
        try:
            csec = config['common-broker']
            commconfig.assignConf(csec, blktype)
            config.remove_section('common-broker')
            print("Found common broker configuration parameters")
            found = True
        except KeyError:
            pass

    return config, commconfig, found


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
