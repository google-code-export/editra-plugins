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

# Local Imports
from PyToolsUtils import get_packageroot, get_modulepath
from AbstractSyntaxChecker import AbstractSyntaxChecker
import ToolConfig
from finder import GetSearchPath

# Editra Imports
import util
import ebmlib

#-----------------------------------------------------------------------------#

class PythonSyntaxChecker(AbstractSyntaxChecker):
    def __init__(self, variabledict, filename):
        super(PythonSyntaxChecker, self).__init__(variabledict, filename)

        # Attributes
        self.dirvarfile = variabledict.get("DIRVARFILE")
        self.pylintargs = ['-r', 'n']
        pylintrc = variabledict.get("PYLINTRC")
        if pylintrc:
            pylintrc = "--rcfile=%s" % pylintrc
            self.pylintargs = self.pylintargs + [pylintrc]
        else:
            # Use built-in configuration
            dlist = ToolConfig.GetConfigValue(ToolConfig.TLC_DISABLED_CHK)
            if dlist is not None and len(dlist):
                if len(dlist) > 1:
                    disable = ",".join(dlist)
                else:
                    disable = dlist[0]
                self.pylintargs += ["-d", "%s" % disable]
        self.addedpythonpaths = variabledict.get("ADDEDPYTHONPATHS")
        self.nopylinterror = u"***  FATAL ERROR: Pylint is not installed"
        self.nopylintmoduleerror = u"***  FATAL ERROR: Cannot import Pylint module!!! ***"

        def do_nothing():
            pass
        self.startcall = variabledict.get("STARTCALL")
        if not self.startcall:
            self.startcall = do_nothing
        self.endcall = variabledict.get("ENDCALL")
        if not self.endcall:
            self.endcall = do_nothing

    @staticmethod
    def getnewsyspath(extrapaths):
        # Find Python path imports
        dllpath = ["C:\\Python26\\DLLs"]
        base = ToolConfig.GetConfigValue("module_base")
        return GetSearchPath(base) + extrapaths + dllpath

    def DoCheck(self):
        """Run pylint"""
        self.startcall()

        # traverse downwards until we are out of a python package
        childPath, parentPath = get_packageroot(self.filename)
        absparentPath = os.path.abspath(parentPath)

        # Start pylint
        allargs = self.pylintargs + ['%s' % get_modulepath(childPath)]
        util.Log("Full Pylint Arguments: %s" % repr(allargs))

        # Pylint output
        class PylintOutput:
            def __init__(self, rows):
                self.rows = rows
                self.rowsdict = {}
                self.regex = re.compile(r"(.*):(.*): \[([A-Z])[, ]*(.*)\] (.*)")

            def write(self, line):
                # remove pylintrc warning
                if line.startswith(u"PYTHONPATH"):
                    util.Log(line)
                    return
                if line.startswith(u"No config file found"):
                    return
                matcher = self.regex.match(line)
                if matcher is None:
                    return
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
                    mtyperows = self.rowsdict.get(mtype)
                    if not mtyperows:
                        mtyperows = {}
                        self.rowsdict[mtype] = mtyperows
                    linenorows = mtyperows.get(lineno)
                    if not linenorows:
                        linenorows = set()
                        mtyperows[lineno] = linenorows
                    linenorows.add(outtext)
                except:
                    self.rows.append((mtype, outtext, linenostr))

        rows = []
        pylint_output = PylintOutput(rows)
        original_exit = sys.exit
        original_path = sys.path
        def no_exit(arg):
            pass
        util.Log("Original sys path: %s" % repr(sys.path))
        sys.path = [".", absparentPath] + self.getnewsyspath(self.addedpythonpaths)
        util.Log("New sys path: %s" % repr(sys.path))
        from pylint import lint
        from pylint.reporters.text import ParseableTextReporter

        sys.exit = no_exit
        lint.Run(allargs, reporter=ParseableTextReporter(pylint_output))
        sys.exit = original_exit
        sys.path = original_path

        # The parseable line format is '%(path)s:%(line)s: [%(sigle)s%(obj)s] %(msg)s'
        # NOTE: This would be cleaner if we added an Emacs reporter to pylint.reporters.text ..
        if self.addedpythonpaths:
            rows.append((u"***", u"Using PYTHONPATH + %s"\
                          % u", ".join(self.addedpythonpaths), u"NA"))
        rows.append((u"***", u"Pylint arguments: %s" % allargs, u"NA"))
        rows.append((u"***", u"Directory Variables file: %s" % self.dirvarfile, u"NA"))
        for mtype in sorted(pylint_output.rowsdict):
            mtyperows = pylint_output.rowsdict[mtype]
            for lineno in sorted(mtyperows):
                linenorows = mtyperows[lineno]
                for outtext in sorted(linenorows):
                    rows.append((mtype, outtext, lineno))

        self.endcall()
        util.Log("[PyLint][info] Pylint command finished running")
        return rows
