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
from AbstractSyntaxChecker import AbstractSyntaxChecker
import LintConfig

# Editra Imports
import util
import ebmlib

#-----------------------------------------------------------------------------#

class PythonSyntaxChecker(AbstractSyntaxChecker):
    def __init__(self, variabledict, filename):
        super(PythonSyntaxChecker, self).__init__(variabledict, filename)

        # Attributes
        self.dirvarfile = variabledict.get("DIRVARFILE")
        # inithook = "--init-hook=\"import os; print 'PYTHONPATH=%s' % os.getenv('PYTHONPATH');\""
        self.runpylint = " -f parseable  -r n" # %s " % inithook
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
        self.nopylinterror = u"***  FATAL ERROR: Pylint is not installed"
        self.nopylinterror += u" or is not in path!!! ***"

        def do_nothing():
            pass
        self.startcall = variabledict.get("STARTCALL")
        if not self.startcall:
            self.startcall = do_nothing
        self.endcall = variabledict.get("ENDCALL")
        if not self.endcall:
            self.endcall = do_nothing

    def DoCheck(self):
        """Run pylint"""
        self.startcall()

        # Figure out what Pylint to use
        # 1) First check configuration
        # 2) Second check for it on the path
        lintpath = LintConfig.GetConfigValue(LintConfig.PLC_LINT_PATH)
        if lintpath is None or not os.path.exists(lintpath):
            lintpath = None
            res = ebmlib.Which("pylint")
            if res is not None:
                lintpath = "pylint"

        # No configured pylint and its not on the PATH
        if lintpath is None:
            return [(u"No Pylint", self.nopylinterror, u"NA"),]

        inithook = " --init-hook=\"import os; print 'PYTHONPATH=%s' % os.getenv('PYTHONPATH');\""
        self.runpylint += inithook

        # traverse downwards until we are out of a python package
        fullPath = os.path.abspath(self.filename)
        parentPath, childPath = os.path.dirname(fullPath), os.path.basename(fullPath)

        while parentPath != "/" and os.path.exists(os.path.join(parentPath, '__init__.py')):
            childPath = os.path.join(os.path.basename(parentPath), childPath)
            parentPath = os.path.dirname(parentPath)

        # Start pylint
        cmdline = lintpath + self.runpylint
        plint_cmd = "%s%s" % (cmdline, '"%s"' % childPath)
        util.Log("[PyLint][info] Starting command: %s" % plint_cmd)
        util.Log("[Pylint][info] Using CWD: %s" % parentPath)
        process = Popen(plint_cmd,
                        shell=True, stdout=PIPE, stderr=STDOUT,
                        cwd=parentPath)
        p = process.stdout

        # The parseable line format is '%(path)s:%(line)s: [%(sigle)s%(obj)s] %(msg)s'
        # NOTE: This would be cleaner if we added an Emacs reporter to pylint.reporters.text ..
        regex = re.compile(r"(.*):(.*): \[([A-Z])[, ]*(.*)\] (.*)")
        rows = []
        if self.addedpythonpaths:
            rows.append((u"***", u"Using PYTHONPATH + %s"\
                          % u", ".join(self.addedpythonpaths), u"NA"))
        rows.append((u"***", u"Pylint command line: %s" % cmdline, u"NA"))
        rows.append((u"***", u"Directory Variables file: %s" % self.dirvarfile, u"NA"))
        for line in p:
            # remove pylintrc warning
            util.Log("[PyLint][info] Reading output: %s" % line)
            if line.startswith(u"PYTHONPATH"):
                continue
            if line.startswith(u"No config file found"):
                continue
            matcher = regex.match(line)
            if matcher is None:
                continue
            mtypeabr = matcher.group(3)
            lineno = matcher.group(2)
            classmethod = matcher.group(4)
            mtext = matcher.group(5)
            if mtypeabr == u"E" or mtypeabr == u"F":
                mtype = u"Error"
            else:
                mtype = u"Warning"
            outtext = mtext
            if classmethod:
                outtext = u"[%s] %s" % (classmethod, outtext)
            rows.append((mtype, outtext, lineno))

        p.close()
        self.endcall()
        util.Log("[PyLint][info] Pylint command finished running")
        return rows
