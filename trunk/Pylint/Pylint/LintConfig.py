# -*- coding: utf-8 -*-
###############################################################################
# Name: LintConfig.py                                                         #
# Purpose: PyLint Configuration Panel                                         #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2010 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################

"""Launch User Interface"""
__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id: $"
__revision__ = "$Revision: $"

#-----------------------------------------------------------------------------#
# Imports
import wx

# Editra Imports
from profiler import Profile_Get, Profile_Set

#-----------------------------------------------------------------------------#
# Configuration Keys
PYLINT_CONFIG = "Pylint.Config"
PLC_AUTO_RUN = "AutoRun"

# Globals
_ = wx.GetTranslation
#-----------------------------------------------------------------------------#

def GetConfigValue(key):
    """Get a value from the config"""
    config = Profile_Get(PYLINT_CONFIG, default=dict())
    return config.get(key, None)

#-----------------------------------------------------------------------------#

class LintConfigPanel(wx.Panel):
    def __init__(self, parent):
        super(LintConfigPanel, self).__init__(parent)

        # Attributes
        modebox = wx.StaticBox(self, label=_("Run Mode"))
        self._modesz = wx.StaticBoxSizer(modebox, wx.VERTICAL)
        self._config = Profile_Get(PYLINT_CONFIG, default=dict())
        self._autorb = wx.RadioButton(self, label=_("Automatic"))
        tooltip = _("Automatically rerun on save, document change, and file load")
        self._autorb.SetToolTipString(tooltip)
        self._manualrb = wx.RadioButton(self, label=_("Manual"))
        tooltip = _("Only run when requested")
        self._manualrb.SetToolTipString(tooltip)
        mode = self._config.get(PLC_AUTO_RUN, False)
        self._autorb.SetValue(mode)
        self._manualrb.SetValue(not mode)

        # Setup
        
        # Layout
        self.__DoLayout()

        # Event Handlers
        self.Bind(wx.EVT_RADIOBUTTON, self.OnCheckBox, self._autorb)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnCheckBox, self._manualrb)

    def __DoLayout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        self._modesz.Add(self._autorb, 0, wx.ALL, 5)
        self._modesz.Add(self._manualrb, 0, wx.ALL, 5)
        sizer.Add(self._modesz, 0, wx.ALL|wx.EXPAND, 10)

        self.SetSizer(sizer)

    def OnCheckBox(self, evt):
        evt_obj = evt.GetEventObject()
        if evt_obj in (self._autorb, self._manualrb):
            self._config[PLC_AUTO_RUN] = self._autorb.GetValue()
        else:
            evt.Skip()
            return

        Profile_Set(PYLINT_CONFIG, self._config)
