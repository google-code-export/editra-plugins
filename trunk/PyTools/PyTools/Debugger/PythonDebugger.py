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
import pkg_resources

# Local Imports
from PyTools.Common import ToolConfig
from PyTools.Common.PyToolsUtils import PyToolsUtils
from PyTools.Common.AsyncProcessCreator import AsyncProcessCreator
from PyTools.Debugger.AbstractDebugger import AbstractDebugger
from PyTools.Debugger.DebugClient import DebugClient

# Editra Imports
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
        self.rpdb2args = ["-d", "--pwd=%s" % DebugClient.password]
        if not self.debuggerargs:
            self.debuggerargs = variabledict.get("DEBUGGERARGS")
        self.pythonpath = variabledict.get("PYTHONPATH")
        self.nopythonerror = u"***  FATAL ERROR: No local Python configured or found"
        self.debugclient = DebugClient()
        self.debuggee = None
        self.processcreator = None

    def RunDebuggee(self):
        """Run rpdb2args"""

        # Figure out what Python to use
        # 1) First check configuration
        # 2) Second check for it on the path
        localpythonpath = ToolConfig.GetConfigValue(ToolConfig.TLC_PYTHON_PATH)
        if not localpythonpath:
            localpythonpath = PyToolsUtils.GetDefaultPython()

        # No configured Python
        if not localpythonpath:
            return [(u"No Python", self.nopythonerror, u"NA"),]
        util.Log("[PyDbg][info] Using Python: %s" % localpythonpath)

        # No rpdb2 found in plugin
        if not pkg_resources.resource_exists("PyTools.Debugger", "test.py"):
            return ["No rpdb2 found"]

        rpdb2_script = pkg_resources.resource_filename("PyTools.Debugger", "test.py")

        childPath, parentPath = PyToolsUtils.get_packageroot(self.filename)

        # Start rpdb2
        cmdargs = ""
        self.debuggee = childPath
        if self.debuggerargs:
            cmdargs = self.debuggerargs.split(" ")
            for i, cmd in enumerate(cmdargs):
                if cmd == "%SCRIPT%":
                    cmdargs[i] = self.debuggee
                elif cmd == "%MODULE%":
                    self.debuggee = PyToolsUtils.get_modulepath(childPath)
                    cmdargs[i] = self.debuggee

            cmdargs = self.rpdb2args + cmdargs
        else:
            cmdargs = self.rpdb2args + [self.debuggee,]
        allargs = cmdargs
        if self.programargs:
            allargs = allargs + self.programargs.split(" ")
        rpdb2_cmd = [localpythonpath, rpdb2_script] + allargs
        text = ""
        if self.pythonpath:
            text += u"Using PYTHONPATH + %s" % u", ".join(self.pythonpath)
        text += u"\nRpdb2 command line: %s" % " ".join(rpdb2_cmd)
        text += u"\nDirectory Variables file: %s\n" % self.dirvarfile
        self.debuggeewindow.SetText(text)
        self.processcreator = AsyncProcessCreator(self.debuggeewindow, "PyDbg", parentPath, rpdb2_cmd, self.pythonpath)
        self.processcreator.start()
        util.Log("[PyDbg][info] Rpdb2 command running")

    def RunDebugger(self):
        if self.processcreator and self.debuggee:
            util.Log("[PyDbg][info] Debugger attaching")
            self.debugclient.attach(self.debuggee)
            util.Log("[PyDbg][info] Debugger attached")
        self.processcreator.restorepath()
        #self.processcreator.Abort()
        util.Log("[PyDbg][info] Debugger exiting")
