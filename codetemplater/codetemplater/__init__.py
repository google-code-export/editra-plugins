#from __future__ import with_statement #avoiding with statement for 2.4 compatibility
"""Applies Code Templates for regularly-used design patterns."""
__author__ = "Erik Tollerud"
__version__ = "0.1"

import wx                   
import iface
import plugin
from os import path
from wx.stc import EVT_STC_USERLISTSELECTION
from ed_glob import CONFIG,SB_INFO,ID_RELOAD_ENC
from ed_menu import EdMenu
from profiler import Profile_Get, Profile_Set
_ = wx.GetTranslation

from templates import TemplateEditorDialog,load_default_templates,PROFILE_KEY_TEMPLATES
PROFILE_KEY_POPUP = 'CodeTemplater.Popupshortcut'

ID_EDIT_TEMPLATES  = wx.NewId()
ID_SHOW_TEMPLATES = wx.NewId()


 
class CodeTemplater(plugin.Plugin):
    """Adds a Save/Load Session Menu Item to the MainWindow File Menu"""
    plugin.Implements(iface.MainWindowI)  
    
    def __init__(self,*args,**kwargs):
        plugin.Plugin.__init__(self,*args,**kwargs)
        self.templates = dict([(t.name,t) for t in load_default_templates()])
        
    def PlugIt(self, parent):
        """Implements MainWindowI's PlugIt Method"""
        self.mw = parent
        
        self._log = wx.GetApp().GetLog()
        self._log("[CodeTemplater][info] Starting codetemplater")
        
        self.templatemenu = submenu = EdMenu()
        popupshortcut = Profile_Get(PROFILE_KEY_POPUP)
        if popupshortcut is None:
            popupshortcut = 'Ctrl+Alt+Space'
        submenu.Append(ID_SHOW_TEMPLATES,_('Show Code Templates')+'\t'+popupshortcut)
        submenu.AppendSeparator()    
        submenu.Append(ID_EDIT_TEMPLATES,_('Edit Templates...'),
                 _('Open a Dialog to Edit the Templates Currently in Use'))
                       
        toolmenu = self.mw.GetMenuBar().GetMenuByName("tools")
        toolmenu.AppendSubMenu(submenu,'Code Templates',_('Insert Code Templates into Document'))
        
        self.mw.Bind(EVT_STC_USERLISTSELECTION,self.OnTemplate)
        
    def GetMenuHandlers(self):
        return [(ID_EDIT_TEMPLATES,self.OnEdit),
                (ID_SHOW_TEMPLATES,self.OnShow)]
    
    def GetUIHandlers(self):
        return []
            
    def OnShow(self, evt):
        if evt.GetId() == ID_SHOW_TEMPLATES:
            lst = self.templates.keys()
            lst.sort()
            wx.GetApp().GetCurrentBuffer().UserListShow(1, u' '.join(lst))
        else:
            evt.skip()
            
    def OnTemplate(self,evt):
        current_buffer = wx.GetApp().GetCurrentBuffer()
        res = self.templates[evt.GetText()].DoTemplate(current_buffer)
            
    def OnEdit(self, evt):
        if evt.GetId() == ID_EDIT_TEMPLATES:
            self._log("[CodeTemplater][info] Loading Editor Dialog")
            
            dlg = TemplateEditorDialog(self.mw,self,-1,_('Code Template Editor'))
            
            dlg.ShowModal()
            dlg.edpanel.applyTemplateInfo()
            dlg.Destroy()
            self._log("[CodeTemplater][info] Completed Editing")
        else:
            evt.Skip()
            
    def AddTemplate(self,templateobj):
        """
        if template is already present, it will be overwritten
        """
        self.templates[templateobj.name] = templateobj
    def RemoveTemplate(self,templateobjorkey):
        if isinstance(templateobjorkey,basestring):
            delk = templateobjorkey
        else:
            delk = None
            for k,v in self.templates.iteritems():
                if v is templateobjorkey:
                    delk = k
                    break
            if delk is None:
                raise KeyError('template '+str(templateobjorkey)+' not found')
        del self.templates[delk]
                



def GetConfigObject():
    return CodeTemplaterConfig()
 
class CodeTemplaterConfig(plugin.PluginConfigObject):
    """Plugin configuration object."""
    def GetConfigPanel(self, parent):
        """Get the configuration panel for this plugin
        @param parent: parent window for the panel
        @return: wxPanel
 
        """
        return CodeTemplaterConfigPanel(parent)
 
    def GetLabel(self):
        """Get the label for this config panel
        @return string
 
        """
        return _('Code Templater Configuration')

ID_POPUP_SHORTCUT = wx.NewId()

class CodeTemplaterConfigPanel(wx.Panel):
    def __init__(self,parent, *args, **kwargs):
        wx.Panel.__init__(self,parent, *args, **kwargs)
        return
        
        basesizer = wx.BoxSizer(wx.VERTICAL)
        
        label = wx.StaticText(self, -1, _("Template Popup shortcut (requires restart):"))
        basesizer.Add(label, 0, wx.ALL, 5)
        
        
        
        profshortcut = Profile_Get(PROFILE_KEY_POPUP)
        if profshortcut is None:
            profshortcut = 'Ctrl+Alt+Space'
        self.shortcuttxt = wx.TextCtrl(self,ID_POPUP_SHORTCUT,profshortcut)
        basesizer.Add(shortcuttxt,1,wx.GROW|wx.ALL, 5)
        
        self.Bind(wx.EVT_TEXT, self.OnTextChange)
        
    def OnTextChange(self,evt):
        if evt.GetId() == ID_POPUP_SHORTCUT:
            text = self.shortcuttxt.GetValue()
            Profile_Set(PROFILE_KEY_POPUP,text)
        else:
            evt.Skip()
 

