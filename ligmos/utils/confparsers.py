# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on Tue Feb 27 12:46:30 2018
#
#  @author: rhamilton

from __future__ import division, print_function, absolute_import

from collections import OrderedDict

try:
    import configparser as conf
except ImportError:
    import ConfigParser as conf

from . import common


def parseConfFile(filename, debug=False):
    """
    Parse the .conf file that gives the setup per instrument
    Returns an ordered dict of Instrument classes that the conf file
    has 'enabled=True'
    """
    try:
        config = conf.SafeConfigParser()
        config.read_file(open(filename, 'r'))
    except IOError as err:
        common.nicerExit(err)

    # We might have a common section, so treat it real nice.
    #   May or may not be in there depending on the conf file.
    #   Might have to deal with capitalization at some point.
    try:
        csec = config['common']
        # Use it to fill the common/core data structure
        commconfig = common.commonParams(conf=csec)
        # Now purge the common section out so it doesn't get confused
        config.remove_section('common')
    except KeyError:
        print("No 'common' configuration section found!")
        commconfig = None

    sections = config.sections()
    tsections = ' '.join(sections)
    if debug is True:
        print("Found the following sections in the configuration file:")
        print("%s\n" % tsections)

    return config, commconfig


def getActiveConfiguration(filename, conftype=common.baseTarget,
                           debug=False):
    """
    """
    config, commconfig = parseConfFile(filename, debug=debug)

    # Last check of the proper/expected type of the given configtype
    #   could be any of the *Target classes in ligmos.utils.common
    # Note that since we pass in the class reference itself (as configtype)
    #   we can check issubclass() INSTEAD of isinstance.
    if not issubclass(conftype, common.baseTarget):
        print("Expected a subclass of ligmos.utils.common.baseTarget...")
        print("Returning None but you really should abort and fix this.")
        return None

    print("Attempting to assign the configuration parameters...")

    # Ultimate storage locations of final results
    #   inlist will contain everything
    #   idict will contain only those with [eng,]enabled == True
    inlist = []
    idict = OrderedDict()

    for each in config.sections():
        print("Applying '%s' section of conf. file..." % (each))
        inst = conftype()
        inst = common.assignConf(inst, conf=config[each])
        # inst = common.addCommonBlock(inst, common=commconfig)

        inlist.append(inst)
        # Need to add None as well to help for the case where I forget
        #   to put an 'enabled' line in a new flavor of conf file...
        if inst.enabled is True or inst.enabled is None:
            idict.update({inst.name: inst})

    # return idict, commconfig
    return idict, commconfig


def parsePassConf(filename, idict, debug=False):
    """
    """
    # Not supporting a [common] section for passwords so ditch it
    config, _ = parseConfFile(filename)

    for each in idict.keys():
        # Get the username for this instrument
        iuser = idict[each].user
        # Now see if we have a password for this username
        try:
            passw = config[iuser]['pw']
        except KeyError:
            if debug is True:
                print("Username %s has no password!" % (iuser))
            passw = None

        idict[each].addPass(passw)

    return idict
