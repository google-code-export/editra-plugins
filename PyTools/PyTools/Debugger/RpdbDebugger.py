# -*- coding: utf-8 -*-
# Name: RpdbDebugger.py
# Purpose: Debug Client
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
##############################################################################
""" RpdbDebugger functions """

__version__ = "0.2"
__author__ = "Mike Rans"
__svnid__ = "$Id: RpdbDebugger.py 1025 2010-12-24 18:30:23Z rans@email.com $"
__revision__ = "$Revision: 1025 $"

#-----------------------------------------------------------------------------#
# Imports
import sys
import os.path
import wx

# Editra Libraries
import util
from profiler import Profile_Get, Profile_Set

# Local Imports
import rpdb2
from PyTools.Debugger.RpdbStateManager import RpdbStateManager
from PyTools.Debugger.RpdbBreakpointsManager import RpdbBreakpointsManager
# We'll have one class for each registered callback like synchronicity

class RpdbDebugger(object):
    fAllowUnencrypted = True
    fRemote = False
    host = "localhost"
    fAttach = True
    fchdir = False
    password = "editra123"

    def __init__(self):
        super(RpdbDebugger, self).__init__()
        self.sessionmanager = rpdb2.CSessionManager(RpdbDebugger.password, \
            RpdbDebugger.fAllowUnencrypted, RpdbDebugger.fRemote, RpdbDebugger.host)
        self.breakpointmanager = RpdbBreakpointsManager(self.sessionmanager)
        self.statemanager = RpdbStateManager(self.sessionmanager, self.breakpointmanager)
        self.pid = None

    def set_breakpointfn(self, getbreakpointfn):
        self.breakpointmanager.getbreakpoints = getbreakpointfn
    
    def set_mainwindowid(self, mwid):
        self.statemanager.mainwindowid = mwid
        
    def set_pid(self, pid):
        self.pid = str(pid)
    
    def attach(self):
        if self.pid:
            util.Log("[PyDbg][info] Trying to Attach")
            self.sessionmanager.attach(self.pid, encoding = rpdb2.detect_locale())
            util.Log("[PyDbg][info] Running")
            self.pid = None

    def get_breakpointmanager(self):
        return self.breakpointmanager
    
    def do_detach(self):
        try:
            self.sessionmanager.detach()
        except rpdb2.NotAttached:
            pass

    def do_stop(self):
        try:
            self.sessionmanager.stop_debuggee()
        except rpdb2.NotAttached:
            pass

    def do_restart(self):
        try:
            self.sessionmanager.restart()
        except rpdb2.NotAttached:
            pass

    def do_jump(self, lineno):
        try:
            self.sessionmanager.request_jump(lineno)
        except rpdb2.NotAttached:
            pass

    def do_go(self):
        try:
            self.sessionmanager.request_go()
        except rpdb2.NotAttached:
            pass

    def do_break(self):
        try:
            self.sessionmanager.request_break()
        except rpdb2.NotAttached:
            pass

    def do_step(self):
        try:
            self.sessionmanager.request_step()
        except rpdb2.NotAttached:
            pass

    def do_next(self):
        try:
            self.sessionmanager.request_next()
        except rpdb2.NotAttached:
            pass

    def do_return(self):
        try:
            self.sessionmanager.request_return()
        except rpdb2.NotAttached:
            pass

    def run_toline(self, filename, lineno):
        try:
            self.sessionmanager.request_go_breakpoint(filename, '', lineno)
        except rpdb2.NotAttached:
            pass

    def disable_breakpoint(self, bpid):
        try:
            self.sessionmanager.disable_breakpoint([bpid], True)
        except rpdb2.NotAttached:
            pass

    def enable_breakpoint(self, bpid):
        try:
            self.sessionmanager.enable_breakpoint([bpid], True)
        except rpdb2.NotAttached:
            pass

    def clear_breakpoints(self):
        try:
            self.sessionmanager.delete_breakpoint([], True)
        except rpdb2.NotAttached:
            pass
        
    def set_breakpoint(self, filepath, lineno, exprstr = "", enabled=True):
        try:
            return self.sessionmanager.set_breakpoint(filepath, '', lineno, enabled, exprstr)
        except rpdb2.NotAttached:
            return None

    def delete_breakpoint(self, bpid):
        try:
            self.sessionmanager.delete_breakpoint([bpid], True)
        except rpdb2.NotAttached:
            pass
