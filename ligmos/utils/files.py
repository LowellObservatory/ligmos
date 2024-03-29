# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on Thu Feb 15 16:56:52 2018
#
#  @author: rhamilton

from __future__ import division, print_function, absolute_import

import re
import glob
import fnmatch

from shutil import rmtree
from os.path import basename, exists, expanduser, join, isdir
try:
    from os import walk, statvfs, remove, makedirs, listdir
except ImportError:
    from os import walk, remove, makedirs, listdir

import numpy as np

from . import dateutils as dstuff


def getDirListing(loc, window=2, oldest=7300, dirmask="[0-9]{8}.*",
                  comptype='newer', debug=False):
    """
    """
    # Regular expression for the format of a data directory
    #   [0-9] == any number from 0-9
    #   {8}   == match the previous set 8 times
    #   .     == any character
    # Default: "[0-9]{8}." matches 20180123a

    # Make sure the location has an ending / to make stuff easier
    if loc[-1] != "/":
        loc += "/"

    # Need number of seconds in the day window since calendar math sucks
    window *= 24. * 60. * 60.
    oldest *= 24. * 60. * 60.

    # Same setup as Peter's obsactive scripts now basically
    dirlist = [join(loc, x) for x in listdir(loc) if isdir(join(loc, x))]
    # At least attempt to sort it sensibly
    dirlist = sorted(dirlist)
    # if debug is True:
    #     print(dirlist)

    # Need to match loc+dirmask to only catch directories ending in the
    #   regular expression (well, after the last slash)
    validdirs = [it for it in dirlist if re.fullmatch(loc + dirmask, it)]
    if debug is True:
        print(validdirs)

    # Make a list of dirs in which their parsed date < than param. window
    if comptype.lower() == 'newer':
        recentmod = [it for it in validdirs if dstuff.dateDiff(it) < window]
    elif comptype.lower() == 'older':
        recentmod = [it for it in validdirs if dstuff.dateDiff(it) >= window]
        # One final round of this to allow downselecting of files
        #   older than window but less than oldest
        recentmod = [it for it in recentmod if dstuff.dateDiff(it) <= oldest]

    if debug is True:
        if recentmod != []:
            print("Directories found:")
            for each in recentmod:
                print(each)
        else:
            print("No dirs matching \"%s\" found at %s" % (dirmask, loc))

#    # dirlist on remote host, with file attributes
#    dirlist = sftp.listdir_attr('.')
#
#    # Selecting only directories, which have 'd' in their permission string
#    #   it should also ignore dotfile directories
#    dirsonly = [it for it in dirlist if (it.longname[0] == 'd') and
#                                        (it.filename[0] != '.')]
#
#    # Select the directories which have been modified "recently"
#    #   where "recently" is a parameter defined elsewhere
#    now = dt.datetime.timestamp(dt.datetime.utcnow())
#    recentmod = [it for it in dirsonly if (now - it.st_mtime) < recently]
#
#    for each in recentmod:
#        print(each.longname)

    return recentmod


def recursiveSearcher(base, fileext="*.fits"):
    """
    Given a directory to start in and an optional extension to check for,
    recursively search through the directories underneath and return the
    list of files that match the fileext.
    """
    # Quick hack to make it work with multiple file extensions
    allexts = fileext.split(",")

    curdata = []
    # The 2nd return value is dirnames but we don't need them so dump to _
    for root, _, filenames in walk(str(base)):
        for ext in allexts:
            for filename in fnmatch.filter(filenames, ext):
                curdata.append(join(root, filename))

    # It'll be sorted by name, but it's better than nothing
    return sorted(curdata)


def checkDir(loc, debug=False):
    """
    Given a location, check to make sure that location actually exists
    somewhere accessible on the filesystem.

    TODO: Merge/replace this with checkOutDir ?
    """
    # First expand any relative paths (expanduser takes ~/ to a real place)
    fqloc = expanduser(loc)

    # Make sure the place actually exists...
    if exists(fqloc) is False:
        if debug is True:
            print("%s doesn't exist!" % (fqloc))
        return False, fqloc
    else:
        return True, fqloc


def checkOutDir(outdir, getList=True):
    """
    TODO: Merge/replace this with checkDir ?
    """
    # Check if the directory exists, and if not, create it!
    try:
        makedirs(outdir)
    except FileExistsError:
        pass
    except OSError as err:
        # Something bad happened. Could be a race condition between
        #   the check for dirExists and the actual creation of the
        #   directory/tree, but scream and signal an abort.
        print(str(err))
    except Exception as err:
        # Catch for other (permission?) errors just to be safe for now
        print(str(err))

    flist = None
    if getList is True:
        flist = sorted(glob.glob(outdir + "/*"))
        flist = [basename(each) for each in flist]

    return flist


def checkFreeSpace(loc, debug=False):
    """
    Given a filesystem location (/home/), return the amount of free space
    on the partition that contains that location
    """
    # First expand any relative paths (expanduser takes ~/ to a real place)
    fqloc = expanduser(loc)

    # Make sure the place actually exists...
    if checkDir(loc) is False:
        if debug is True:
            print("Fatal Error: %s doesn't exist!" % (loc))
        return None
    else:
        try:
            # TODO: statvfs kinda sucks and I should replace this with psutil
            osstatvfs = statvfs(fqloc)
        except Exception as e:
            if debug is True:
                print("Unknown Error: %s" % (str(e)))
            return None

        if debug is True:
            print("Checking free space at %s ..." % (fqloc))

        # Check overall size, originally in bytes so /1024./1024./1024. == GiB
        # Cribbing from the IEEE:
        #   f_frsize   Fundamental file system block size [in bytes].
        #   f_blocks   Total num of blocks on file system in units of f_frsize.
        #   f_bfree    Total num of free blocks.
        #   f_bavail   Num of free blocks available to non-privileged process.
        total = (osstatvfs.f_frsize * osstatvfs.f_blocks)/1024./1024./1024.

        # Check free, same as above. NEED .f_bavail because
        #   .f_bfree is counting some space that's actually reserved
        free = (osstatvfs.f_frsize * osstatvfs.f_bavail)/1024./1024./1024.

        if debug is True:
            print("Total: %.2f\nFree: %.2f" % (total, free))
            print("%.0f%% remaining" % (100. * free/total))

        # Make it a bit more clear what is what via a dictionary
        retdict = {'path': None,
                   'total': None,
                   'free': None,
                   'percentfree': None}
        retdict['path'] = loc
        retdict['total'] = total
        retdict['free'] = free
        retdict['percentfree'] = np.around(free/total, decimals=2)

        return retdict


def deleteOldFiles(fdict):
    """
    fdict should be a dictionary whose key is the filename and the
    value is that filename's determined age (in seconds)
    """
    for key in fdict:
        print("Deleting %s since it's too old (%.3f hr)" %
              (key, fdict[key]/60./60.))
        try:
            remove(key)
        except OSError as err:
            # At least see what the issue was
            print(str(err))


def deleteOldDirectories(fdict):
    """
    fdict should be a dictionary whose key is the filename and the
    value is that filename's determined age (in seconds)
    """
    for key in fdict:
        print("Deleting %s since it's too old (%.3f hr)" %
              (key, fdict[key]/60./60.))
        try:
            rmtree(key)
        except OSError as err:
            # At least see what the issue was
            print(str(err))


def findOldFiles(inloc, fmask, now, maxage=24., dtfmt="%Y%j%H%M%S%f"):
    """
    'maxage' is in hours

    Returns two dictionaries, one for the current (young) files and one
    for the out-of-date (old) files. Both dicts are set up the same,
    with the keys being the filenames and their values their determined age.
    """
    maxage *= 60. * 60.
    flist = sorted(glob.glob(inloc + fmask))

    goldenoldies = {}
    youngsters = {}
    for each in flist:
        diff = dstuff.getFilenameAgeDiff(each, now, dtfmt=dtfmt)
        if diff > maxage:
            goldenoldies.update({each: diff})
        else:
            youngsters.update({each: diff})

    return youngsters, goldenoldies
