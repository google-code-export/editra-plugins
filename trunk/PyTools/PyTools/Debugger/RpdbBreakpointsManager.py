# -*- coding: utf-8 -*-
# Name: RpdbBreakpointsManager.py
# Purpose: Debug Breakpoints
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
##############################################################################
""" RpdbBreakpointsManager functions """

__version__ = "0.2"
__author__ = "Mike Rans"
__svnid__ = "$Id: DebugState.py 1025 2010-12-24 18:30:23Z rans@email.com $"
__revision__ = "$Revision: 1025 $"

#-----------------------------------------------------------------------------#
# Imports
import sys
import os.path
import wx

# Editra Libraries
import util

# Local Imports
import rpdb2

class RpdbBreakpointsManager(object):
    def __init__(self, sessionmanager):
        super(RpdbBreakpointsManager, self).__init__()
        self.sessionmanager = sessionmanager
        self.breakpoints_set = False
        self.getbreakpoints = None
    
    def loadbreakpoints(self):
        try:
            self.sessionmanager.load_breakpoints()
            util.Log("[DbgBp][info] Removing old breakpoints")
            self.sessionmanager.delete_breakpoint([], True)
        except IOError:
            util.Log("Failed to load old breakpoints")
        util.Log("Setting breakpoints: (Path, Line No, Enabled)")
        breakpoints = self.getbreakpoints()
        for filepath in breakpoints:
            linenos = breakpoints[filepath]
            for lineno in linenos:
                enabled, exprstr, bpid = linenos[lineno]
                bpid = self.sessionmanager.set_breakpoint(filepath, '', lineno, enabled, exprstr)
                linenos[lineno] = enabled, exprstr, bpid
                util.Log("%s, %d, %s, %s" % (filepath, lineno, enabled, exprstr))
        self.breakpoints_set = True
        self.output("\nDebugger attached. Breakpoints set. Program output starts now...\n")
        self.sessionmanager.request_go()
