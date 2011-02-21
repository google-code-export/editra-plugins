# -*- coding: utf-8 -*-
# Name: DebugClient.py
# Purpose: Debug Client
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
##############################################################################
""" DebugClient functions """

__version__ = "0.2"
__author__ = "Mike Rans"
__svnid__ = "$Id: DebugClient.py 1025 2010-12-24 18:30:23Z rans@email.com $"
__revision__ = "$Revision: 1025 $"

#-----------------------------------------------------------------------------#
# Imports
import sys
import os.path
import wx

# Local Imports
from PyTools.Debugger import rpdb2
from PyTools.Debugger.DebugState import DebugState
from PyTools.Debugger.DebugBreakpoint import DebugBreakpoint
# We'll have one class for each registered callback like synchronicity

class DebugClient(object):
    fAllowUnencrypted = True
    fRemote = False
    host = "localhost"
    fAttach = True
    fchdir = False
    password = "123"

    def __init__(self):
        super(DebugClient, self).__init__()
        self.m_session_manager = rpdb2.CSessionManager(DebugClient.password, \
            DebugClient.fAllowUnencrypted, DebugClient.fRemote, DebugClient.host)
        self.state = DebugState(self.m_session_manager)
        self.breakpoint = DebugBreakpoint(self.m_session_manager)

    def attach(self, debuggee):
        self.m_session_manager.attach(debuggee, encoding = rpdb2.detect_locale())

    def do_detach(self, event):
        self.m_session_manager.detach()

    def do_stop(self, event):
        self.m_session_manager.stop_debuggee()

    def do_restart(self, event):
        self.m_session_manager.restart()

    def do_jump(self, event):
        pass

    def do_go(self, event):
        self.m_session_manager.request_go()

    def do_break(self, event):
        self.m_session_manager.request_break()

    def do_step(self, event):
        self.m_session_manager.request_step()

    def do_next(self, event):
        self.m_session_manager.request_next()

    def do_return(self, event):
        self.m_session_manager.request_return()

    def do_goto(self, event):
        #(filename, lineno) = self.m_code_viewer.get_file_lineno()
        filename = "TOGET"
        lineno = 99999
        self.m_session_manager.request_go_breakpoint(filename, '', lineno)

    def do_disable(self, event):
        self.m_session_manager.disable_breakpoint([], True)

    def do_enable(self, event):
        self.m_session_manager.enable_breakpoint([], True)

    def do_clear(self, event):
        self.m_session_manager.delete_breakpoint([], True)

    def do_load(self, event):
        # self.m_session_manager.with_callback(self.callback_load).load_breakpoints()
        pass

    def do_save(self, event):
        # self.m_session_manager.with_callback(self.callback_save).save_breakpoints()
        pass
