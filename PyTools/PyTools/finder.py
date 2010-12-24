###############################################################################
# Name: finder.py
# Purpose: Components to find modules source files by name
# Author: Rudi Pettazzi <rudi.pettazzi@gmail.com>
# Copyright: (c) 2009 Cody Precord <staff@editra.org>
# License: wxWindows License
###############################################################################

__author__ = "Rudi Pettazzi <rudi.pettazzi@gmail.com>"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#--------------------------------------------------------------------------#
# Dependancies

import os
import os.path
import re
import sys


#--------------------------------------------------------------------------#
# Globals

def GetSearchPath(base=None):
    """ Build the modules search path for a given python installation.
    The path is a list containing:
     1) sys.prefix/lib
     2) sys.prefix/lib/site-packages
     3) The PYTHONPATH elements, if any
     4) The paths defined into .pth files found into the above directories.
    By default, the installation is the one that is running this module.
    Use the argument prefix to override (e.g.: prefix='C:\Python25'
    or prefix='/usr/lib/python2.5')
    """
    # installation-dependent default
    if base == None:
        if sys.platform == 'win32':
            base = sys.prefix
        else:
            base = '%s/lib/python%s' % (sys.prefix, sys.version[:3])

    if sys.platform == 'win32':
        path = [ os.path.join(base, 'lib'),
                 os.path.join(base, 'lib', 'site-packages') ]
    else:
        path = [ base, os.path.join(base, 'site-packages') ]
        
    # PYTHONPATH (if defined, it must prepend the default path)
    pythonpath = os.environ.get('PYTHONPATH')
    if pythonpath:
        tmp = path
        path = pythonpath.split(os.pathsep)
        path.extend(tmp)

    spath = path

    # Parse '.pth' found on the search path and add their entries to search
    # path. For example, on windows with wxPython installed, "site-packages/wx.pth"
    # contains the line 'wx-<version>-mws-unicode' and 'wx-<version>-mws-unicode is
    # a subdirectory of site-packages.
    for dir in path:
        if not os.path.isdir(dir):
            continue
        for f in os.listdir(dir):
            if os.path.splitext(f)[1] == '.pth':
                list = _ParsePth(dir, f)
                if list: spath.extend(list)

    return spath


def _ParsePth(dirname, filename):
    """ Extracts paths from .pth files
    @param dirname: the directory that contains this .pth file
    @param filename: the .pth filename
    @return: a list with the valid paths defined into the .pth file.
    """
    lst = []
    for line in open(os.path.join(dirname, filename)).readlines():
        line = line.strip()
        if line[0] == '#' or line[0].startswith('import'):
            continue
        pth = os.path.join(dirname, line)
        if os.path.isdir(pth):
            lst.append(pth)
    return lst

#--------------------------------------------------------------------------#

class ModuleFinder(object):
    """
    This component finds the source file of all the modules matching
    a given name, using one of the following strategies:
    1) loading the module with __import__ (0 or 1 results).
    This strategy is limited because it doesn't work if Editra is 
    run from the binary installer and it can search only within 
    the same python version that is actually running the editor.
    2) traversing the filesystem starting at a given search path
    (0 or N results) and matching files and packages using various
    criteria described below. This is the default strategy.

    For maximum execution and correctness performance, in the future, we could
    use a persistent index to lookup the modules.

    """

    # TODO: the extensions for source files could also be retrieved from
    #       syntax.syntax.ExtensionRegister
    _SRC_EXT = '.py', '.pyw'
    _BYTECODE_EXT = '.pyc', '.pyo'

    # a path we can safely skip for better performance
    _WXLOCALE = os.path.join('wx', 'locale')

    def __init__(self, searchpath):
        """
        @param searchpath: list of modules search path
        """
        self._searchpath = searchpath
        self._sources = []

    def Find(self, text):
        """ Find the source files of modules matching text.
        @param text: the module name
        @return: a list with the module sources path if any, an empty list
        otherwise
        """
        if not text:
            return []
        else:
            return self._Find(text);

    def _Find(self, text):
        """Find pure python modules matching text by walking the search path 
        and doing a prefix match (case insensitive). 
        If text contains the module package - for ex: 'compiler.ast' - the search
        is narrowed to that package/subdirectory, otherwise a free search is
        executed.
        
        Examples:
            find compiler.ast => compiler/ast.py
            find ast.py => compiler/ast.py
            find compiler.email => no result
            find string => string.py, StringIO.py, et al.
            find os.string => None
            find email.mime => email/mime/__init__.py
            find mime => email/mime/__init__.py, mimetools.py, et al.

        @param text: the module name
        @return: a list of source files matching text, an empty list if no 
        source has been found.
        """
        parts = text.split('.')
        text = parts[-1]
        pattern = re.compile(text, re.I)

        self._sources = []

        for path in self._searchpath:
            if os.path.isdir(path):
                #print 'Analysing search path %s' % path
                pkgs = parts[:-1]
                if pkgs:
                    self._PackageSearch(path, pattern, text, pkgs)
                else:
                    self._FreeSearch(path, pattern, text)
        return self._sources
    
    def _FreeSearch(self, path, pattern, text):
        """Traverse the given path looking for a module matching text.
        The possible matches are:
        1) **/text*.py 
        2) **/text/__init__.py (ex: ctypes => ctypes/__init__.py)

        @param path: the current directory absolute path
        @param text: the module name to match
        """
        for filename in os.listdir(path):
            fqdn = os.path.join(path, filename)
            if os.path.isfile(fqdn) and self._IsPatternMatch(filename, pattern):
                self._sources.append(fqdn)
            elif os.path.isdir(fqdn) and not self._Skip(fqdn):
                pkgsource = os.path.join(fqdn, '__init__.py')
                if filename == text and os.path.exists(pkgsource):
                    self._sources.append(pkgsource)
                else:
                    self._FreeSearch(fqdn, pattern, text)
    
    def _PackageSearch(self, path, pattern, text, ns):
        """ Traverse the given path looking for a module matching text 
        into the namespace ns. The possible matches are:
        1) ns.text*.py
        2) ns.text/__init__.py
        3) ns.py (ex: os.path => os.py)
        4) ns/__init__.py
        
        XXX: maybe 3) and 4) should be added to the result only if nothing
        matches 1) or 2)

        @param path: the current directory absolute path
        @param text: the module name to match (if the user entered a 
                     dotted module, text contains only the last token).
        @param ns:   a list with the namespace parts relative to current path
                     For example, if text is 'email.mime.audio', ns should be
                     [ 'email', 'mime' ]
        """        
        if ns:
            pkg = ns.pop(0)
        else:
            pkg = None

        for filename in os.listdir(path):
            fqdn = os.path.join(path, filename)
            if os.path.isfile(fqdn):
                if not pkg and self._IsPatternMatch(filename, pattern) or self._IsExactMatch(filename, pkg):
                    self._sources.append(fqdn)
            elif os.path.isdir(fqdn) and not self._Skip(fqdn):
                pkgsource = os.path.join(fqdn, '__init__.py')
                if filename == text and os.path.exists(pkgsource):
                    self._sources.append(pkgsource)
                    break # definately looking for this
                elif filename == pkg:
                    self._PackageSearch(fqdn, pattern, text, ns)        

    def _IsExactMatch(self, filename, text):
        """ @return: true if filename is a source module and its name 
        without extension is equals to text"""
        parts = os.path.splitext(filename)
        return parts[1] in ModuleFinder._SRC_EXT and text == parts[0]
        
    def _IsPatternMatch(self, filename, pattern):
        """ @return: true if filename is a source module and its name
        without extension matches pattern"""
        parts = os.path.splitext(filename)
        return parts[1] in ModuleFinder._SRC_EXT and pattern.match(parts[0])

    def _Skip(self, path):
        return path in self._searchpath or path.endswith(ModuleFinder._WXLOCALE)

#--------------------------------------------------------------------------#
# Test

if __name__ == '__main__':
    import time

    t1 = time.clock()
    path = GetSearchPath()
    t2 = time.clock()
    print 'Module search path: %s' % path
    print 'Path loading took %f seconds.' % (t2-t1)

    mf = ModuleFinder(path)
    t1 = time.clock()
    result = mf.Find('mime', False)
    t2 = time.clock()
    print 'Found %s' % result
    print 'Find took %f seconds.' % (t2-t1)


