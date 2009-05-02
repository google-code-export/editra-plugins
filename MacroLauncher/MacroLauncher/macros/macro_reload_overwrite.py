
# -*- coding: utf-8 -*-

name = 'reload#'
type = 'plugin'
desc = 'reloads all plugins that have the doreload() method'


import os
import sys

def run(txtctrl, log = None, **kwargs):
  editra_dir = os.path.sep.join(os.path.dirname(__file__).split(os.path.sep)[0:-3])
  if (editra_dir) in sys.path:
    pass
  else:
    sys.path.append(editra_dir)
  import wx
  plgmgr = wx.GetApp().GetPluginManager()
  for plugin in plgmgr.GetPlugins():
      plugin = plgmgr.__getitem__(plugin)
      
      if plugin:
          if hasattr(plugin, 'doreload'):
              log('Reloading plugin: %s' % str(plugin))
              #plugin.doreload()
              wx.CallAfter(plugin.doreload)
              #wx.CallLater(1000, plugin.doreload)

      
