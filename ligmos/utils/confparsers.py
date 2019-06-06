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


def parseConfFile(filename, debug=False, abort=True):
    """
    Parse the .conf file that gives the setup per instrument
    Returns an ordered dict of Instrument classes that the conf file
    has 'enabled=True'

    If abort is True, than an IOError on the configuration file
    will sink the code and stop immediately. False will return None.
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

    # We might have a common section, so treat it real nice.
    #   May or may not be in there depending on the conf file.
    #   Might have to deal with capitalization at some point.

    # Set up the final resting place for the common database/broker params
    commconfig = common.commonParams()

    try:
        # Do we have a database config?
        csec = config['common-database']

        # Use it to fill the common/core data structure. Since it's a
        #   class method it'll just fill up the class appropriately.
        commconfig.assignConf(csec, 'database')

        # Now purge the common section out so it doesn't get confused
        config.remove_section('common-database')
        print("Found common database configuration parameters")
        dbinfo = True
    except KeyError:
        dbinfo = False

    # Second verse, same as the first
    try:
        csec = config['common-broker']
        commconfig.assignConf(csec, 'broker')
        config.remove_section('common-broker')
        print("Found common broker configuration parameters")
        bkinfo = True
    except KeyError:
        bkinfo = False

    # Final step to flag common block stuff
    if (dbinfo is False) and (bkinfo is False):
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


def parsePassConf(filename, idict, cblk=None, debug=False):
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

            idict[each] = common.addPass(idict[each], passw)

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


def parseBrokerConfig(conffile, passfile, conftype, debug=True):
    """
    I hate how I'm going about all of these conf. parsers. It's a damn mess!
    This one is for spinning up a broker connection without depending
    on the structure in workers.toServeMan().
    """
    # idict: dictionary of parsed config file
    # cblk: common block from config file
    # Read in the configuration file and act upon it
    idict, cblk = getActiveConfiguration(conffile,
                                         conftype=conftype,
                                         debug=debug)

    # If there's a password file, associate that with the above
    if passfile is not None:
        idict, cblk = parsePassConf(passfile, idict,
                                    cblk=cblk,
                                    debug=debug)

    return idict, cblk
