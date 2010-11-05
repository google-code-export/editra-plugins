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
        self._config = Profile_Get(PYLINT_CONFIG, default=dict())
        self._updatecb = wx.CheckBox(self, label=_("Automatic Mode"))
        tooltip = _("Automatically rerun on save, document change, and file load")
        self._updatecb.SetToolTipString(tooltip)
        self._updatecb.SetValue(self._config.get(PLC_AUTO_RUN, False))

        # Setup
        
        # Layout
        self.__DoLayout()

        # Event Handlers
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckBox, self._updatecb)

    def __DoLayout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.Add(self._updatecb, 0, wx.ALL, 5)

        self.SetSizer(sizer)

    def OnCheckBox(self, evt):
        evt_obj = evt.GetEventObject()
        value = evt_obj.GetValue()
        if evt_obj == self._updatecb:
            self._config[PLC_AUTO_RUN] = value
        else:
            evt.Skip()
            return

        Profile_Set(PYLINT_CONFIG, self._config)
