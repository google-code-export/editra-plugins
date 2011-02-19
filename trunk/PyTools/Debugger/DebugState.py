# -*- coding: utf-8 -*-
# Name: DebugState.py
# Purpose: Debug State
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
##############################################################################
""" DebugState functions """

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
from Debugger import rpdb2

class DebugState(object):
    def __init__(self, m_session_manager):
        super(DebugState, self).__init__()
        self.m_state = rpdb2.STATE_DETACHED
        self.m_session_manager = m_session_manager
        state = self.m_session_manager.get_state()
        self.update_state(rpdb2.CEventState(state))

        event_type_dict = {rpdb2.CEventState: {}}
        self.m_session_manager.register_callback(self.update_state, event_type_dict, fSingleUse = False)

    def update_state(self, event):
        wx.CallAfter(self.callback_state, event)

    def callback_state(self, event):
        old_state = self.m_state
        self.m_state = event.m_state

        # change menu or toolbar items displayed according to state eg. running, paused etc.

        state_text = self.m_state
        if state_text == rpdb2.STATE_BROKEN:
            state_text = rpdb2.STR_STATE_BROKEN

        # set status info about state to state_text.upper()

        if self.m_state == rpdb2.STATE_DETACHED:
            # clear all debugging stuff as we have finished
            pass
        elif (old_state in [rpdb2.STATE_DETACHED, rpdb2.STATE_DETACHING, rpdb2.STATE_SPAWNING, rpdb2.STATE_ATTACHING]) and (self.m_state not in [rpdb2.STATE_DETACHED, rpdb2.STATE_DETACHING, rpdb2.STATE_SPAWNING, rpdb2.STATE_ATTACHING]):
            try:
                serverinfo = self.m_session_manager.get_server_info()
                # we are debugging serverinfo.m_filename

                f = self.m_session_manager.get_encryption()
            except rpdb2.NotAttached:
                f = False

        if self.m_state == rpdb2.STATE_BROKEN:
            # we hit a breakpoint
            # show the stack viewer, threads viewer, namespace viewer
            pass
        elif self.m_state == rpdb2.STATE_ANALYZE:
            # we are analyzing an exception
            # show the stack viewer and namespace viewer
            pass
        else:
            # any other state
            # don't show any viewers
            pass

