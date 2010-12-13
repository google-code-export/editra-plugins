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
from AbstractSyntaxChecker import AbstractSyntaxChecker
import LintConfig
import os, re
from subprocess import Popen, PIPE

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
        self.runpylint = "pylint -f parseable -r n %s " % inithook
        pylintrc = variabledict.get("PYLINTRC")
        if pylintrc:
            self.runpylint = "%s--rcfile=%s " % (self.runpylint, pylintrc)
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
        res = ebmlib.Which("pylint")
        if not res:
            return ((u"No Pylint", self.nopylinterror, u"NA"),)
        # traverse downwards until we are out of a python package
        fullPath = os.path.abspath(self.filename)
        parentPath, childPath = os.path.dirname(fullPath), os.path.basename(fullPath)

        while parentPath != "/" and os.path.exists(os.path.join(parentPath, '__init__.py')):
            childPath = os.path.join(os.path.basename(parentPath), childPath)
            parentPath = os.path.dirname(parentPath)

        # Start pylint
        process = Popen("%s%s" % (self.runpylint, childPath),
                        shell=True, stdout=PIPE, stderr=PIPE,
                        cwd=parentPath)
        p = process.stdout

        # The parseable line format is '%(path)s:%(line)s: [%(sigle)s%(obj)s] %(msg)s'
        # NOTE: This would be cleaner if we added an Emacs reporter to pylint.reporters.text ..
        regex = re.compile(r"(.*):(.*): \[([A-Z])[, ]*(.*)\] (.*)")
        rows = []
        if self.addedpythonpaths:
            rows.append((u"***", u"Using PYTHONPATH + %s"\
                          % u", ".join(self.addedpythonpaths), u"NA"))
        rows.append((u"***", u"Pylint command line: %s" % self.runpylint, u"NA"))
        rows.append((u"***", u"Directory Variables file: %s" % self.dirvarfile, u"NA"))
        for line in p:
            # remove pylintrc warning
            if line.startswith(u"PYTHONPATH"):
                util.Log(line)
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
        return rows
