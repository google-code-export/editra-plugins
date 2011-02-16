# -*- coding: utf-8 -*-
# Name: DebugBreakpoint.py
# Purpose: Debug Breakpoints
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
##############################################################################
""" DebugBreakpoint functions """

__version__ = "0.2"
__author__ = "Mike Rans"
__svnid__ = "$Id: DebugState.py 1025 2010-12-24 18:30:23Z rans@email.com $"
__revision__ = "$Revision: 1025 $"

#-----------------------------------------------------------------------------#
# Imports
import sys
import os.path
import wx

# Local Imports
import rpdb2

class DebugBreakpoint(object):
    def __init__(self, m_session_manager):
        super(DebugBreakpoint, self).__init__()
        self.m_session_manager = m_session_manager

        event_type_dict = {rpdb2.CEventBreakpoint: {}}
        self.m_session_manager.register_callback(self.update_bp, event_type_dict, fSingleUse = False)

    def update_bp(self, event):
        pass
#        if self.m_pos_filename is None:
#            return

#        fposition_timeout = time.time() - self.m_last_position_time > POSITION_TIMEOUT

#        if event.m_action == rpdb2.CEventBreakpoint.SET and fposition_timeout:
#            if self.m_cur_filename == event.m_bp.m_filename:
#                lineno = event.m_bp.m_lineno
#                self.m_viewer.EnsureVisibleEnforcePolicy(lineno - 1)
#                self.m_viewer.GotoLine(lineno - 1)

#        self.set_markers()
