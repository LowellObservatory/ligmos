# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 7 Jun 2019
#
#  @author: rhamilton

"""Manipulating already parsed configuration files
"""

from __future__ import division, print_function, absolute_import


def assignComm(conf, comm, confkey='connection'):
    """
    comm should be a dict of baseTarget objects

    conf should be a dict of objects of some ligmos.utils.classes class
    """
    for sec in conf.keys():
        # Look for the specified key that tells us which comm section to
        #   stuff into it for later use
        try:
            # Get the *value* of that attribute
            ck = getattr(conf[sec], confkey)

            # Does comm contain ck?  Let's check!
            #   Remember - comm is a dict so we can't use getattr
            cobj = comm[ck]
        except KeyError as err:
            print(str(err))
            ck = None
            cobj = None

        # Actually set the confkey to the thing we found in comm
        setattr(conf[sec], confkey, cobj)

    return conf


def assignPasses(conf, passes, debug=True):
    """
    Probably very, very, very insecure.

    Checks to see if there is a 'user' property in the given config, and
    then tries to get a 'password' property from the given passes.  If
    the user is None, the check is skipped.  If the password doesn't exist,
    the check is aborted.  In either of those cases, the resulting config
    section will *lack* a password attribute completely.
    """
    # Get the big list 'o sections that we will check
    csects = conf.sections()

    for each in csects:
        con = conf[each]
        # See if we can find username for this instrument
        try:
            iuser = con['user']
            # Quick and dirty typecheck
            if iuser.lower() == 'none':
                iuser = None
        except KeyError:
            iuser = None

        # Now see if we have a password for this username
        if iuser is not None:
            try:
                passw = passes[iuser]['password']
            except KeyError:
                if debug is True:
                    print("Username %s has no password!" % (iuser))
                # This must be a string! Otherwise it'll throw a TypeError
                #   at you when you actually try to assign it to the section
                passw = 'None'

            # Actually update the configuration section with this password
            conf[each]['password'] = passw

    return conf


def assignConf(conf, obj, backfill=False, debug=False):
    """
    Given an arbitrary class reference and a parsed configuration file (conf),
    assign keys from the latter into parameters in the former.

    Assumes that ALL keys in the class are present in the configuration; if
    they aren't, then they're set to ```None``` and caught/announced in the
    ```KeyError``` exception below.

    If 'backfill' is False, parameters that are in the *configuration file*
    but not in the given class are *ignored* completely.  If True,
    they're added to the given class with a warning.
    """
    # Make an instance of our given object/class
    classy = obj()

    # Get the list of parameters in the instance (classy) given class (obj)
    oparams = list(classy.__dict__.keys())

    # Now do the same for the configuration object (conf)
    cparams = list(conf.keys())

    # Check to see if there are any that are in the class but not in the conf
    #   If there are, keydiffs will != [] and they'll be shoved into the class
    #   with a warning if backfill is True, otherwise they're ignored entirely
    keydiffs = list(set(cparams) - set(oparams))

    for key in classy.__dict__:
        try:
            # Remember: key is from the input class here
            kval = conf[key]

            # Check to see if it's a comma-separated-list, and other parsing
            #   stuff happens to check for none/true/false
            nkval = valChecks(kval)

            # Actually set the parameter (key) in the class (classy)
            #   to the value that we found/cleaned up (nkval)
            setattr(classy, key, nkval)
        except KeyError:
            # This means that
            if debug is True:
                print("Improper config; missing configuration key %s" % (key))
            # Just set it to None and move on with our lives
            setattr(classy, key, None)

    if backfill is True:
        # If there are any, that is
        if keydiffs != []:
            for orphan in keydiffs:
                orphVal = valChecks(conf[orphan])
                print("Setting orphan object key %s to %s" % (orphan, orphVal))
                setattr(classy, orphan, orphVal)

    return classy


def valChecks(kval):
    """
    """
    # It'll always be a string by this point, so it should always
    #   have a .split() method.  If not, someone else has mucked about
    #   with the configuration object before it got here.
    kval = kval.strip().split(",")

    # Trim off leading/trailing whitespace for each. Also make sure
    #    that it's a list, no matter what, so we can itterate over it.
    kval = [kv.strip() for kv in kval]

    # kval is now definitely a list
    allval = []
    for val in kval:
        # Some icky type checks
        if val.lower() == "none":
            nkval = None
        elif val.lower() == 'false':
            nkval = False
        elif val.lower() == 'true':
            nkval = True
        else:
            nkval = val
        # Put it into a list in case there's more than one
        allval.append(nkval)

    # If there's just one thing that we found, return it alone. Otherwise
    #   return the full list of stuff
    if len(allval) == 1:
        nkval = allval[0]
    else:
        nkval = allval

    return nkval
