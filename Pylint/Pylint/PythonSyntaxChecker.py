# -*- coding: utf-8 -*-
# Name: PythonSyntaxChecker.py
# Purpose: Pylint plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
##############################################################################
""" Pylint module for Python data """

__author__ = "Mike Rans"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports
import os
import sys
import re
from subprocess import Popen, PIPE, STDOUT

if sys.platform == 'win32':
    import win32process

# Local Imports
from AbstractSyntaxChecker import AbstractSyntaxChecker
import LintConfig
from finder import GetSearchPath, ModuleFinder

# Editra Imports
import util
import ebmlib

#-----------------------------------------------------------------------------#

class PythonSyntaxChecker(AbstractSyntaxChecker):
    def __init__(self, variabledict, filename):
        super(PythonSyntaxChecker, self).__init__(variabledict, filename)

        # Attributes
        self.dirvarfile = variabledict.get("DIRVARFILE")
        inithook = "--init-hook=\"import os; print 'PYTHONPATH=%s' % os.getenv('PYTHONPATH');\""
        self.runpylint = " -f parseable  -r n %s " % inithook
        pylintrc = variabledict.get("PYLINTRC")
        if pylintrc:
            pylintrc = "--rcfile=%s " % pylintrc
            self.runpylint = self.runpylint + pylintrc
        else:
            # Use built-in configuration
            dlist = LintConfig.GetConfigValue(LintConfig.PLC_DISABLED_CHK)
            if dlist is not None and len(dlist):
                if len(dlist) > 1:
                    disable = ",".join(dlist)
                else:
                    disable = dlist[0]
                self.runpylint += ("-d %s " % disable)
        self.addedpythonpaths = variabledict.get("ADDEDPYTHONPATHS")
        self.nopythonerror = u"***  FATAL ERROR: No local Python configured or found"
        self.nopylinterror = u"***  FATAL ERROR: No Pylint found in local Python"

    def GetEnvironment(self, localpythonpath, pythonsearchpath):
        environment = os.environ.copy()
        if sys.platform == 'win32':
            environment["PATH"] = str(environment["PATH"])
            platformpaths = ["%s%sDLLs" % (localpythonpath, os.sep)]
        elif platform.mac_ver()[0]:
            platformpaths = []
        else:
            platformpaths = []
        allpaths = pythonsearchpath + self.addedpythonpaths + platformpaths
        environment["PYTHONPATH"] = str(os.pathsep.join(allpaths))
        return environment    
        
    def DoCheck(self):
        """Run pylint"""

        # Figure out what Python to use
        # 1) First check configuration
        # 2) Second check for it on the path
        localpythonpath = LintConfig.GetConfigValue(LintConfig.PLC_LOCAL_PYTHON)
        if not LintConfig.CheckLocalPython(localpythonpath):
            localpythonpath = LintConfig.GetDefaultPython()

        # No configured Python
        if not localpythonpath:
            return [(u"No Python", self.nopythonerror, u"NA"),]

        util.Log("[PyLint][info] Using Python: %s" % localpythonpath)
        pythonsearchpath = GetSearchPath(localpythonpath)
        util.Log("[PyLint][info] Using Python Searchpath: %s" % pythonsearchpath)
        mf = ModuleFinder(pythonsearchpath)
        results = mf.Find("pylint")
        # No pylint found in local Python
        if not results:
            return [(u"No Pylint", self.nopylinterror, u"NA"),]

        # traverse downwards until we are out of a python package
        fullPath = os.path.abspath(self.filename)
        parentPath, childPath = os.path.dirname(fullPath), os.path.basename(fullPath)

        while parentPath != "/" and os.path.exists(os.path.join(parentPath, '__init__.py')):
            childPath = os.path.join(os.path.basename(parentPath), childPath)
            parentPath = os.path.dirname(parentPath)

        # Start pylint
        lintpath = "%s%sscripts%spylint" % (localpythonpath, os.sep, os.sep)
        if sys.platform == 'win32':
            lintpath = "%s.bat" % lintpath
        cmdline = lintpath + self.runpylint
        plint_cmd = "%s%s" % (cmdline, '"%s"' % childPath)
        util.Log("[PyLint][info] Starting command: %s" % plint_cmd)
        util.Log("[Pylint][info] Using CWD: %s" % parentPath)
        environment = self.GetEnvironment(localpythonpath, pythonsearchpath)
        util.Log("[Pylint][info] Using env: %s" % repr(environment))
        creationflags = 0
        if sys.platform == 'win32':
            creationflags = win32process.CREATE_NO_WINDOW
        process = Popen(plint_cmd,
                        bufsize=1048576, stdout=PIPE, stderr=PIPE, 
                        cwd=parentPath, env=environment, 
                        creationflags=creationflags)
        stdoutdata, stderrdata = process.communicate()
        util.Log("[Pylint][info] stdout %s" % stdoutdata)
        util.Log("[Pylint][info] stderr %s" % stderrdata)
        # The parseable line format is '%(path)s:%(line)s: [%(sigle)s%(obj)s] %(msg)s'
        # NOTE: This would be cleaner if we added an Emacs reporter to pylint.reporters.text ..
        regex = re.compile(r"(.*):(.*): \[([A-Z])[, ]*(.*)\] (.*)%s" % os.linesep)
        rows = []
        if self.addedpythonpaths:
            rows.append((u"***", u"Using PYTHONPATH + %s"\
                          % u", ".join(self.addedpythonpaths), u"NA"))
        rows.append((u"***", u"Pylint command line: %s" % cmdline, u"NA"))
        rows.append((u"***", u"Directory Variables file: %s" % self.dirvarfile, u"NA"))
        rowsdict = {}
        for matcher in regex.finditer(stdoutdata):
            if matcher is None:
                continue
            mtypeabr = matcher.group(3)
            linenostr = matcher.group(2)
            classmethod = matcher.group(4)
            mtext = matcher.group(5)
            if mtypeabr == u"E" or mtypeabr == u"F":
                mtype = u"Error"
            else:
                mtype = u"Warning"
            outtext = mtext
            if classmethod:
                outtext = u"[%s] %s" % (classmethod, outtext)
            try:
                lineno = int(linenostr)
                mtyperows = rowsdict.get(mtype)
                if not mtyperows:
                    mtyperows = {}
                    rowsdict[mtype] = mtyperows
                linenorows = mtyperows.get(lineno)
                if not linenorows:
                    linenorows = set()
                    mtyperows[lineno] = linenorows
                linenorows.add(outtext)
            except:
                rows.append((mtype, outtext, linenostr))
        for mtype in sorted(rowsdict):
            mtyperows = rowsdict[mtype]
            for lineno in sorted(mtyperows):
                linenorows = mtyperows[lineno]
                for outtext in sorted(linenorows):
                    rows.append((mtype, outtext, lineno))

        util.Log("[PyLint][info] Pylint command finished running")
        return rows
