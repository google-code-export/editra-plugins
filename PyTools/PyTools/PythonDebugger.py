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
# Imports

from AbstractDebugger import AbstractDebugger
from PyToolsUtils import get_packageroot, get_modulepath
import ToolConfig
import os
from subprocess import Popen, PIPE

# Editra Imports
import ebmlib
import util

#-----------------------------------------------------------------------------#

class PythonDebugger(AbstractDebugger):    
    def __init__(self, variabledict, filename):
        super(PythonDebugger, self).__init__(variabledict, filename)

        # Attributes
        self.dirvarfile = variabledict.get("DIRVARFILE")
        
        windbgargs = variabledict.get("WINPDBARGS")
        if windbgargs:
            self.winpdbargs = windbgargs
        else:
            self.winpdbargs = ""
            
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

    def Debug(self, debuggerargs, debugargs):
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
        childPath, parentPath = get_packageroot(self.filename)

        # Override directory variables (WINPDBARGS) with GUI debugger args
        if debuggerargs:
            self.winpdbargs = debuggerargs
        # Start winpdb
        if self.winpdbargs.find("%MODULE%") != -1:
            modulepath = get_modulepath(childPath)
            cmdargs = self.winpdbargs.replace("%MODULE%", modulepath)
        else:
            cmdargs = "%s %s" % (self.winpdbargs, '"%s"' % childPath)
        cmdline = "%s %s %s" % (debugpath, cmdargs, debugargs)
        util.Log("Winpdb Command Line: %s" % cmdline)
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
