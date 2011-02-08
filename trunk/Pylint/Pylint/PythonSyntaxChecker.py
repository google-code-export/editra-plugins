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
import re
from subprocess import Popen, PIPE
import wx

if wx.Platform == "__WXMSW__":
    import win32process

# Local Imports
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
        inithook = "--init-hook=\"import os; print 'PYTHONPATH=%s' % os.getenv('PYTHONPATH');\""
        self.runpylint = ["-f", "parseable", "-r", "n", inithook]
        pylintrc = variabledict.get("PYLINTRC")
        if pylintrc:
            pylintrc = ["--rcfile=%s" % pylintrc]
            self.runpylint += pylintrc
        else:
            # Use built-in configuration
            dlist = ToolConfig.GetConfigValue(ToolConfig.TLC_DISABLED_CHK)
            if dlist is not None and len(dlist):
                if len(dlist) > 1:
                    disable = ",".join(dlist)
                else:
                    disable = dlist[0]
                self.runpylint += ["-d", disable]
        self.pythonpath = variabledict.get("PYTHONPATH")
        self.nopythonerror = u"***  FATAL ERROR: No local Python configured or found"
        self.nopylinterror = u"***  FATAL ERROR: No Pylint configured or found"

    def get_pythonpath(self):
        if os.environ.has_key("PYTHONPATH"):
            return os.getenv("PYTHONPATH")
        return None
        
    def DoCheck(self):
        """Run pylint"""

        # Figure out what Python to use
        # 1) First check configuration
        # 2) Second check for it on the path
        localpythonpath = ToolConfig.GetConfigValue(ToolConfig.TLC_PYTHON_PATH)
        if not localpythonpath:
            localpythonpath = ToolConfig.GetDefaultPython()

        # No configured Python
        if not localpythonpath:
            return [(u"No Python", self.nopythonerror, u"NA"),]
        util.Log("[PyLint][info] Using Python: %s" % localpythonpath)

        pylintpath = ToolConfig.GetConfigValue(ToolConfig.TLC_PYLINT_PATH)
        if not pylintpath:
            pylintpath = ToolConfig.GetDefaultPylint(localpythonpath)
        # No pylint found in local Python
        if not pylintpath or not os.path.isfile(pylintpath):
            return [(u"No Pylint", self.nopylinterror, u"NA"),]
        util.Log("[PyLint][info] Using Pylint: %s" % pylintpath)

        childPath, parentPath = get_packageroot(self.filename)

        # Start pylint
        lintpath = [localpythonpath, pylintpath]
        cmdline = lintpath + self.runpylint
        plint_cmd = cmdline + [get_modulepath(childPath)]
        util.Log("[PyLint][info] Starting command: %s" % repr(plint_cmd))
        util.Log("[Pylint][info] Using CWD: %s" % parentPath)
        curpath = None
        if wx.Platform == "__WXMSW__":
            creationflags = win32process.CREATE_NO_WINDOW
            environment = None
            curpath = self.get_pythonpath()
            os.environ["PYTHONPATH"] = os.pathsep.join(self.pythonpath)
        else:
            creationflags = 0
            environment = {}
            if self.pythonpath:
                environment["PYTHONPATH"] = str(os.pathsep.join(self.pythonpath))

        process = Popen(plint_cmd,
                        bufsize=1048576, stdout=PIPE, stderr=PIPE,
                        cwd=parentPath, env=environment,
                        creationflags=creationflags)
        stdoutdata, stderrdata = process.communicate()
        if wx.Platform == "__WXMSW__" and curpath:
            os.environ["PYTHONPATH"] = curpath

        util.Log("[Pylint][info] stdout %s" % stdoutdata)
        util.Log("[Pylint][info] stderr %s" % stderrdata)
        # The parseable line format is '%(path)s:%(line)s: [%(sigle)s%(obj)s] %(msg)s'
        # NOTE: This would be cleaner if we added an Emacs reporter to pylint.reporters.text ..
        regex = re.compile(r"(.*):(.*): \[([A-Z])[, ]*(.*)\] (.*)%s" % os.linesep)
        rows = []
        if self.pythonpath:
            rows.append((u"***", u"Using PYTHONPATH + %s"\
                          % u", ".join(self.pythonpath), u"NA"))
        rows.append((u"***", u"Pylint command line: %s" % " ".join(plint_cmd), u"NA"))
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

def get_packageroot(filepath):
    # traverse downwards until we are out of a python package
    fullPath = os.path.abspath(filepath)
    parentPath, childPath = os.path.dirname(fullPath), os.path.basename(fullPath)

    while parentPath != "/" and os.path.exists(os.path.join(parentPath, '__init__.py')):
        childPath = os.path.join(os.path.basename(parentPath), childPath)
        parentPath = os.path.dirname(parentPath)
    return (childPath, parentPath)

def get_modulepath(childPath):
    return os.path.splitext(childPath)[0].replace(os.path.sep, ".")