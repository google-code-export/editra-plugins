# -*- coding: UTF-8 -*-
###############################################################################
# Name: __init__.py                                                           #
# Purpose: Find and highlight undefined variables in Python code              #
# Author:  Alex Zankevich <alex.zankevich@gmail.com>                          #
# Copyright: (c) 2009 Alex Zankevich <alex.zankevich@gmail.com>               #
# Licence: wxWindows Licence                                                   #
###############################################################################
"""Find and highlight undefined variables in Python code"""

__author__ = "Alex Zankevich"
__version__ = "0.1"

#-----------------------------------------------------------------------------#
# Imports
import os
import re
from StringIO import StringIO
import wx
from wx.stc import STC_MARK_SHORTARROW, STC_INDIC0_MASK

# Editra Imports
import syntax.synglob as synglob
import ed_msg

# Local Imports
from foxtrot import check_vars

#-----------------------------------------------------------------------------#

class HighLight:
    """Class checks undefined variables and highlights them if they exist"""
    def __init__(self, main):
        """
        @param main: MainWindow instance
        """
        self.marknumber = 1
        self.main = main
        self._log = wx.GetApp().GetLog()
        
    def PlugIt(self):
        """Install varchecker plugin"""
        self._log("[pytools][info] Installing module varchecker")
        ed_msg.Subscribe(self.unhighlight,
                            msgtype=ed_msg.EDMSG_UI_STC_CHANGED)
        ed_msg.Subscribe(self.check_vars,
                            msgtype=ed_msg.EDMSG_FILE_SAVED)
        self._log("[pytools][debug] Varchecker is successfully installed")

    def check_vars(self, *args):
        """Run checking for variables"""
        self._log('[pytools][debug] EDMSG_ID_FILE_SAVED event has been raised')
        stc = self.get_stc()
        if stc.GetLangId() == synglob.ID_LANG_PYTHON:
            txt = stc.GetText()            
            if type(txt) is unicode:
                self._log('[pytools][debug] converting... ')
                encoding = stc.GetDocument().encoding
                #HACK: restricted compiler module cannot use unicode strings
                txt = txt.encode(encoding)
                encoded = txt
            else:
                self._log('[pytools][debug] is already unicode')
            txt = txt.replace('\r\n', '\n')
            self.highlight(check_vars(txt), encoded)
        
    def get_stc(self):
        """Get stc instance"""
        return self.main.GetNotebook().GetCurrentCtrl()

    def set_markers(self, lines):
        """Set markers at lines
        
        @param lines: list of line numbers
        @type lines: list
        """
        stc = self.get_stc()
        stc.MarkerDefine(self.marknumber, STC_MARK_SHORTARROW, background='red')
        for lineno in lines:
            stc.MarkerAdd(lineno, self.marknumber)
            
    def del_markers(self):
        """Delete all the markers"""
        stc = self.get_stc()
        stc.MarkerDeleteAll(self.marknumber)
        
    def set_indic(self, start, length):
        """Highlight a word by setting an indicator
        
        @param start: number of a symbol where the indicator starts
        @type start: int
        
        @param length: length of the highlighted word
        @type length: int
        """
        stc = self.get_stc()
        stc.IndicatorSetForeground(0, 'red')
        stc.StartStyling(start, STC_INDIC0_MASK)
        stc.SetStyling(length, STC_INDIC0_MASK)
        
    def highlight(self, msglist, txt):
        """Highlight undefined variables using all the messages returned by
        check_vars function
        
        @param msglist: list of foxtrot.msg.Msg instances
        @type msglist: list
        
        @param txt: text encoded to 8-bit encoding 
        @type txt: str
        """
        stc = self.get_stc()
        stc.MarkerDefine(self.marknumber, STC_MARK_SHORTARROW, background='red')
        io = StringIO(txt)
        start = 0
        for index, line in enumerate(io.readlines()):
            lineno = index + 1
            for msg in msglist:
                if msg.lineno == lineno:
                    stc.MarkerAdd(lineno-1, self.marknumber)
                    if msg.msgtype == 'undefined_var':
                        self.indic_var(start, lineno, line, msg.varname)
            start += len(line)
        end = stc.GetTextLength()
        #HACK: without the hack below last undefined variable is not highlighted
        stc.StartStyling(end, STC_INDIC0_MASK)
        stc.SetStyling(0, 0)

    def unhighlight(self, *args):
        """Remove all the markers and indicators"""
        self._log('[pytools][debug] EDMSG_ID_STC_CHANGED event has been raised')
        self.unset_indic()
        self.del_markers()

    def indic_var(self, start, lineno, line, varname):
        """Highlight variable
        
        @param start: number of a symbol from beginnig of the document
                      where higlighting starts
        @type start: int
        
        @param lineno: number of a line where highlighting occurs
        @type lineno: int
        
        @param line: content of a line where highlighting occurs
        @type line: str
        
        @param varname: name of the variable to be highlighted
        @type varname: str
        """
        match = re.search(r'(?<!\.)\b%s\b' %varname, line)
        if match:
            spos, epos = match.span()
            self.set_indic(start + spos, len(varname))

    def unset_indic(self):
        """sRemove all the indicators"""
        stc = self.get_stc()
        stc.StartStyling(0, STC_INDIC0_MASK)
        end = stc.GetTextLength()
        stc.SetStyling(end, 0)
