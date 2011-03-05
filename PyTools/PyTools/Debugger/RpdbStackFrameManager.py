# -*- coding: utf-8 -*-
# Name: RpdbStackFrameManager.py
# Purpose: Debug State
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
##############################################################################
""" RpdbStackFrameManager functions """

__version__ = "0.2"
__author__ = "Mike Rans"
__svnid__ = "$Id: RpdbStackFrameManager.py 1025 2010-12-24 18:30:23Z rans@email.com $"
__revision__ = "$Revision: 1025 $"

#-----------------------------------------------------------------------------#
# Imports
import sys
import os.path
import wx

# Editra Libraries
import ed_msg

# Local Imports
import rpdb2

#----------------------------------------------------------------------------#

class RpdbStackFrameManager(object):
    def __init__(self, rpdb2debugger):
        super(RpdbStackFrameManager, self).__init__()
        self.rpdb2debugger = rpdb2debugger
        self.m_stack = None
        event_type_dict = {rpdb2.CEventStackFrameChange: {}}
        self.rpdb2debugger.sessionmanager.register_callback(self.update_frame, event_type_dict, fSingleUse = False)
        event_type_dict = {rpdb2.CEventStack: {}}
        self.rpdb2debugger.sessionmanager.register_callback(self.update_stack, event_type_dict, fSingleUse = False)
        
    #
    #------------------- Frame Select Logic -------------
    #
    
    def update_frame(self, event):
        wx.CallAfter(self.do_update_frame, event.m_frame_index)

    def do_update_frame(self, index):
        self.do_set_position(index)
#        self.m_stack_viewer.select_frame(index)

    #
    #----------------------------------------------------------
    #
    
    def update_stack(self, event):
        self.m_stack = event.m_stack
        wx.CallAfter(self.do_update_stack, event.m_stack)


    def do_update_stack(self, _stack):
        self.m_stack = _stack

#        self.m_stack_viewer.update_stack_list(self.m_stack)
        
        index = self.rpdb2debugger.sessionmanager.get_frame_index()
        self.do_update_frame(index)


    def do_set_position(self, index):
        s = self.m_stack[rpdb2.DICT_KEY_STACK]
        e = s[-(1 + index)]
        
        filename = e[0]
        lineno = e[1]

        fBroken = self.m_stack[rpdb2.DICT_KEY_BROKEN]
        #event = self.m_stack[rpdb2.DICT_KEY_EVENT]
        if not fBroken:
            return
        if not self.rpdb2debugger.breakpoints_loaded:
            self.rpdb2debugger.breakpointmanager.loadbreakpoints(filename)
            self.rpdb2debugger.breakpoints_loaded = True
            self.rpdb2debugger.do_go(filename, lineno)
            return            
        if self.rpdb2debugger.checkterminate(filename, lineno):
            self.rpdb2debugger.do_go(filename, lineno)
            return
        self.rpdb2debugger.seteditormarkers(filename, lineno)


