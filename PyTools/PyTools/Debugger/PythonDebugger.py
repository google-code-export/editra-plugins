# -*- coding: utf-8 -*-
# Name: PythonDebugger.py
# Purpose: Rpdb2 plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
##############################################################################
""" Rpdb2 module for Python data """

__author__ = "Mike Rans"
__svnid__ = "$Id: PythonDebugger.py 1053 2011-02-08 22:09:37Z rans@email.com $"
__revision__ = "$Revision: 1053 $"

#-----------------------------------------------------------------------------#
# Imports
import os.path
import pkg_resources
from time import sleep

# Local Imports
from PyTools.Common import ToolConfig
from PyTools.Common.PyToolsUtils import PyToolsUtils
from PyTools.Common.PyToolsUtils import RunProcInThread
from PyTools.Common.AsyncProcessCreator import AsyncProcessCreator
from PyTools.Debugger.AbstractDebugger import AbstractDebugger
from PyTools.Debugger.RpdbDebugger import RpdbDebugger
from PyTools.Debugger import RPDBDEBUGGER

# Editra Libraries
import util
import ebmlib
#-----------------------------------------------------------------------------#

class PythonDebugger(AbstractDebugger):
    def __init__(self, variabledict, debuggerargs, programargs, 
        filename, debuggeewindow):
        super(PythonDebugger, self).__init__(variabledict, debuggerargs, 
            programargs, filename, debuggeewindow)

        # Attributes
        self.dirvarfile = variabledict.get("DIRVARFILE")
        self.rpdb2args = ["-d", "--pwd=%s" % RpdbDebugger.password]
        if not self.debuggerargs:
            self.debuggerargs = variabledict.get("DEBUGGERARGS")
        self.pythonpath = variabledict.get("PYTHONPATH")
        self.debuggee = None
        self.processcreator = None

    def RunDebuggee(self):
        """Run rpdb2args"""

        flag, localpythonpath = ToolConfig.GetPythonExecutablePath("PyDbg")

        if not flag:
            # No configured Python
            return [(u"No Python", localpythonpath, u"NA"),]

        # No rpdb2 found in plugin
        if not pkg_resources.resource_exists("rpdb2", "rpdb2.py"):
            return ["No rpdb2 found"]

        rpdb2_script = pkg_resources.resource_filename("rpdb2", "rpdb2.py")

        childPath, parentPath = PyToolsUtils.get_packageroot(self.filename)

        # Start rpdb2
        cmdargs = ""
        debuggee = childPath
        if self.debuggerargs:
            cmdargs = self.debuggerargs.split(" ")
            for i, cmd in enumerate(cmdargs):
                if cmd == "%SCRIPT%":
                    cmdargs[i] = debuggee
                elif cmd == "%MODULE%":
                    debuggee = PyToolsUtils.get_modulepath(childPath)
                    cmdargs[i] = debuggee

            cmdargs = self.rpdb2args + cmdargs
        else:
            cmdargs = self.rpdb2args + [debuggee,]
        allargs = cmdargs
        if self.programargs:
            allargs = allargs + self.programargs.split(" ")
        rpdb2_cmd = [localpythonpath, "-u", rpdb2_script] + allargs
        text = ""
        if self.pythonpath:
            text += u"Using PYTHONPATH + %s" % u", ".join(self.pythonpath)
        text += u"\nRpdb2 command line: %s" % " ".join(rpdb2_cmd)
        text += u"\nDirectory Variables file: %s\n" % self.dirvarfile
        self.debuggeewindow.SetText(text)
        self.debuggeewindow.set_debuggerfn(self.RunDebugger)
        self.processcreator = AsyncProcessCreator(self.debuggeewindow, "PyDbg", parentPath, rpdb2_cmd, self.pythonpath)
        self.processcreator.start()
        util.Log("[PyDbg][info] Rpdb2 command running")

    def RunDebugger(self):                    
        self.debuggeewindow.set_debuggerfn(None)
        self.processcreator.restorepath()
        RPDBDEBUGGER.set_pid(self.processcreator.Process.pid)
        worker = RunProcInThread(RPDBDEBUGGER.attach, None, "Debug")
        worker.start()
