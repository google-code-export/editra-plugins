###############################################################################
# Name: finder.py
# Purpose: Components to find modules source files by name
# Author: Rudi Pettazzi <rudi.pettazzi@gmail.com>
# Copyright: (c) 2009 Cody Precord <staff@editra.org>
# License: wxWindows License
###############################################################################

__author__ = "Rudi Pettazzi <rudi.pettazzi@gmail.com>"
__svnid__ = "$Id: Exp $"
__revision__ = "$Revision:  $"

#--------------------------------------------------------------------------#
# Dependancies

import os
import os.path
import re
import sys

#--------------------------------------------------------------------------#
# Globals

# TODO: this should be called once, at plugin initialization time, or
# on demand, if changing the search path prefix
def getSearchPath(prefix=sys.prefix):
    """ Build the modules search path for a given python installation.
    The path is a list containing:
     1) sys.prefix/Lib
     2) sys.prefix/Lib/site-packages
     3) The PYTHONPATH elements, if any
     4) Not yet implemented: The paths defined into .pth files found into
        the above directories.
    By default, the installation is the one that is running this module.
    Use the argument prefix to override (e.g.: prefix='C:\Python25')
    """
    # installation-dependent default
    path = [ os.path.join(prefix, 'Lib'),
             os.path.join(prefix, 'Lib', 'site-packages') ]

    # PYTHON_PATH
    pythonpath = os.environ.get('PYTHONPATH')
    if pythonpath:
        tmp = path
        path = pythonpath.split(os.pathsep)
        path.extend(tmp)

    spath = path

    # TODO:
    # Parse '.pth' found on the search path and add their entries to search
    # path. For example, on windows with wxPython installed, "site-packages/"
    # contains 'wx.pth' that points to 'wx-<version>-mws-unicode'
    #    for dir in path:
    #        for f in os.listdir(dir):
    #            if os.path.splitext(f)[1] == '.pth':
    #               list = _ParsePth(os.path.join(dir, f))
    #               if list: spath.extend(list)

    return spath

def _ParsePth(filename):
    lst = []
    for line in open(filename).readlines():
        line = line.strip()
        if line[0] != '#' and os.path.isdir(line):
            lst.append(line)
    return lst


#--------------------------------------------------------------------------#

class ModuleFinder(object):
    """
    This component finds the source file of all the modules matching
    a given name, using one of the following strategies:
    1) loading the module with __import__ (0 or 1 results)
    2) traversing a given search path (0 or N results)

    With a persistent index of the modules in place, in the future it
    could use that.
    """

    # TODO: the extensions for source files could also be retrieved from
    #       syntax.syntax.ExtensionRegister
    _SRC_EXTENSIONS = '.py', '.pyw'
    _BYTECODE_EXTENSIONS = '.pyc', '.pyo'

    def __init__(self, searchpath):
        """
        @param searchpath: list of modules search path
        """
        self._searchpath = searchpath
        self._sources = []

    def Find(self, text, useimport=False):
        """ Find the source files of modules matching text.
        @param text: the module name
        @return: a list with the module sources path if any, an empty list
        otherwise
        """
        if useimport:
            return self._FindUseImport(text)
        else:
            return self._Find(text);

    def _Find(self, text):
        """Find modules matching text by walking the search path
        @param text: the module name
        @return: a list with the module source path
        """
        packages = text.split('.')[:-1]

        for path in self._searchpath:
            if os.path.isdir(path):
                # print 'Analysing search path %s' % path
                self._Fill(text, packages[:], path)

        return self._sources

    def _Fill(self, text, packages, path):
        """ Traverse the given path looking for files or packages matching text
        (the module name) or part of it (its package or its containing module)
        @param text: the module name
        @param packages: ...
        @param path: the current directory
        """
        print packages
        pkg = ''
        if packages:
            pkg = packages.pop(0)

        """
        file F analysis:
            1) text matches F name
            2) text fragment matches F name (ex: os.path => os.py)
        dir D analysis:
            3) text matches D name and D contains __init__.py
                (ex: ctypes => cttypes/__init__.py)
            4) text fragment matches D name
            4) expected package matches D: traverse D expecting F or the other
            package name parts
        """
        for fname in os.listdir(path):
            fqdn = os.path.join(path, fname)
            if os.path.isfile(fqdn) and self._FileMatches(fname, text, pkg):
                self._sources.append(fqdn)
            elif os.path.isdir(fqdn) and not fqdn in self._searchpath:
                pkgsource = os.path.join(fqdn, '__init__.py')
                if fname == text and os.path.exists(pkgsource):
                    self._sources.append(pkgsource)
                    break
                elif fname == pkg:
                    # FIXME: if looking for a.b.c and b.c are defined into
                    # a/__init__.py I cannot find them this way
                    self._Fill(text, packages, fqdn)

    def _FileMatches(self, fname, text, pkg):
        parts = os.path.splitext(fname)
        return parts[1] in ModuleFinder._SRC_EXTENSIONS and \
                (parts[0].find(text) != -1 or parts[0] == pkg)

#--------------------------------------------------------------------------#
# old algorithm

    def _FindUseImport(self, name):
        """Find the module source using __import__ with the current runtime
        @param name: the module name
        @return: None or the module source path
        """
        result = []
        if not name:
            return result

        # Import the module to find out its file
        # fromlist needs to be non-empty to import inside packages
        # (e.g. 'wx.lib', 'distutils.core')
        try:
            lst = name.split('.')
            module = __import__(name, lst[:-1])
        except ImportError:
            return result

        fname = getattr(module, '__file__', None)

        if fname:
            # Open source files instead of bytecode
            root, ext = os.path.splitext(fname)
            if ext in ModuleFinder._BYTECODE_EXTENSIONS:
                for se in ModuleFinder._SRC_EXTENSIONS:
                    if os.path.isfile(root + se):
                        fname = root + se
                        break
                else:
                    fname = None
            elif ext not in ModuleFinder._SRC_EXTENSIONS:
                # This is not a pure python module
                fname = None

        if fname:
            result.append(fname)
        return result

#--------------------------------------------------------------------------#
# Test

if __name__ == '__main__':
    import time
    t1 = time.clock()
    path = getSearchPath()
    print 'Module search path: %s' % path
    mf = ModuleFinder(path)
    result = mf.Find('isapi.test.setup.py', False)
    t2 = time.clock()
    print 'Elapsed %f seconds.' % (t2-t1)
    print 'Found %s' % result



