# -*- coding: utf-8 -*-
# Name: PythonDebugger.py
# Purpose: Pylint plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
##############################################################################
""" Debugger module for Python data """

__version__ = "0.2"
__author__ = "Mike Rans"
__svnid__ = "$Id: PythonDebugger.py 1001 2010-12-13 21:16:53Z rans@email.com $"
__revision__ = "$Revision: 1001 $"

#-----------------------------------------------------------------------------#

import os
from AbstractDebugger import AbstractDebugger
import ToolConfig
import ebmlib
import os, re
from subprocess import Popen, PIPE

class PythonDebugger(AbstractDebugger):    
    def __init__(self, variabledict, filename):
        super(PythonDebugger, self).__init__(variabledict, filename)

        # Attributes
        self.dirvarfile = variabledict.get("DIRVARFILE")
        self.winpdbargs = ""

        windbgargs = variabledict.get("WINPDBARGS")
        if windbgargs:
            self.winpdbargs = "%s %s" % (self.winpdbargs, windbgargs)
                        
        self.addedpythonpaths = variabledict.get("ADDEDPYTHONPATHS")
        self.nowinpdberror = u"***  FATAL ERROR: Winpdb is not installed"
        self.nowinpdberror += u" or is not in path!!! ***"
        
        def do_nothing():
            pass
        self.startcall = variabledict.get("STARTCALL")
        if not self.startcall:
            self.startcall = do_nothing
        self.endcall = variabledict.get("ENDCALL")
        if not self.endcall:
            self.endcall = do_nothing

    def Debug(self, debugargs):
        """Run Debugger"""
        self.startcall()

        # Figure out what Winpdb to use
        # 1) First check configuration
        # 2) Second check for it on the path
        debugpath = ToolConfig.GetConfigValue(ToolConfig.TLC_DEBUG_PATH)
        if debugpath is None or not os.path.exists(debugpath):
            debugpath = ebmlib.Which("winpdb.bat")
            if debugpath is None:
                debugpath = ebmlib.Which("winpdb")

        # No configured winpdb and its not on the PATH
        if debugpath is None:
            return ((u"No Winpdb", self.nowinpdberror, u"NA"),)

        # traverse downwards until we are out of a python package
        fullPath = os.path.abspath(self.filename)
        parentPath, childPath = os.path.dirname(fullPath), os.path.basename(fullPath)

        while parentPath != "/" and os.path.exists(os.path.join(parentPath, '__init__.py')):
            childPath = os.path.join(os.path.basename(parentPath), childPath)
            parentPath = os.path.dirname(parentPath)

        # Start winpdb
        if self.winpdbargs.find("%MODULE%") != -1:
            modulepath = os.path.splitext(childPath)[0].replace(os.path.sep, ".")
            cmdargs = self.winpdbargs.replace("%MODULE%", modulepath)
        else:
            cmdargs = "%s %s" % (self.winpdbargs, '"%s"' % childPath)
        cmdline = "%s %s %s" % (debugpath, cmdargs, debugargs)
        process = Popen(cmdline,
                        shell=True,
                        cwd=parentPath)
        rows = []
        if self.addedpythonpaths:
            rows.append((u"***", u"Using PYTHONPATH + %s"\
                          % u", ".join(self.addedpythonpaths), u"NA"))
        rows.append((u"***", u"Winpdb command line: %s" % cmdline, u"NA"))
        rows.append((u"***", u"Directory Variables file: %s" % self.dirvarfile, u"NA"))

        self.endcall()
        return rows
