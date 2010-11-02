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
import os, re
from subprocess import Popen, PIPE

#-----------------------------------------------------------------------------#

class PythonSyntaxChecker(AbstractSyntaxChecker):
    def __init__(self, variabledict, filename):
        super(PythonSyntaxChecker, self).__init__(variabledict, filename)

        # Attributes
        self.dirvarfile = variabledict.get("DIRVARFILE")
        self.runpylint = "pylint -f parseable -r n "
        pylintrc = variabledict.get("PYLINTRC")
        if pylintrc:
            self.runpylint = "%s--rcfile=%s " % (self.runpylint, pylintrc)
        self.addedpythonpaths = variabledict.get("ADDEDPYTHONPATHS")
        self.nopylinterror = "***  FATAL ERROR: Pylint is not installed"
        self.nopylinterror += " or is not in path!!! ***"

    @staticmethod
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
    
    @staticmethod
    def which(program):    
        fpath, _ = os.path.split(program)
        if fpath:
            if PythonSyntaxChecker.is_exe(program):
                return program
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                exe_file = os.path.join(path, program)
                if PythonSyntaxChecker.is_exe(exe_file):
                    return exe_file        
        return None

    def DoCheck(self):
        """Run pylint"""
        res = self.which("pylint")
        if not res:
            return (("No Pylint", self.nopylinterror, "NA"),)
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
            rows.append(("***", "Using PYTHONPATH + %s"\
                          % ", ".join(self.addedpythonpaths), "NA"))
        rows.append(("***", "Pylint command line: %s" % self.runpylint, "NA"))
        rows.append(("***", "Directory Variables file: %s" % self.dirvarfile, "NA"))
        for line in p:
            # remove pylintrc warning
            if line.startswith("No config file found"):
                continue
            matcher = regex.match(line)
            if matcher is None:
                continue
            mtypeabr = matcher.group(3)
            lineno = matcher.group(2)
            classmethod = matcher.group(4)
            mtext = matcher.group(5)
            if mtypeabr == "E" or mtypeabr == "F":
                mtype = "Error"
            else:
                mtype = "Warning"
            outtext = mtext
            if classmethod:
                outtext = "[%s] %s" % (classmethod, outtext)
            rows.append((mtype, outtext, lineno))
 
        p.close()
        return rows
