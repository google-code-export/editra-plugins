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
from ed_msg import Subscribe,EDMSG_UI_STC_USERLIST_SEL,EDMSG_UI_STC_LEXER,EDMSG_UI_NB_CHANGED
from syntax import synglob
from profiler import Profile_Get, Profile_Set
_ = wx.GetTranslation

from templates import TemplateEditorDialog,load_templates
from cfgdlg import CodeTemplaterConfig,PROFILE_KEY_POPUP,PROFILE_KEY_FOLLOW_LANG

ID_EDIT_TEMPLATES  = wx.NewId()
ID_SHOW_TEMPLATES = wx.NewId()

class CodeTemplater(plugin.Plugin):
    """Adds an interface to add Code Templates"""
    plugin.Implements(iface.MainWindowI)  
    
    def __init__(self,*args,**kwargs):
        plugin.Plugin.__init__(self,*args,**kwargs)
        self.templates = load_templates()
        self.currentlang = synglob.ID_LANG_TXT
        
    def PlugIt(self, parent):
        """Implements MainWindowI's PlugIt Method"""
        self.mw = parent
        
        self._log = wx.GetApp().GetLog()
        self._log("[codetemplater][info] Starting codetemplater")
        
        
        self.templatemenu = submenu = EdMenu()
        
        popupshortcut = Profile_Get(PROFILE_KEY_POPUP)
          
        submenu.Append(ID_SHOW_TEMPLATES,_('Show Code Templates')+'\t'+popupshortcut)
        submenu.AppendSeparator()    
        submenu.Append(ID_EDIT_TEMPLATES,_('Edit Templates...'),
                 _('Open a Dialog to Edit the Templates Currently in Use'))
                    
        toolmenu = self.mw.GetMenuBar().GetMenuByName("tools")
        toolmenu.AppendSubMenu(submenu,'Code Templates',_('Insert Code Templates into Document'))
        
        #self.mw.Bind(EVT_STC_USERLISTSELECTION,self.OnTemplate)
        Subscribe(self.OnTemplate,EDMSG_UI_STC_USERLIST_SEL)
        Subscribe(self.OnLexerChange,EDMSG_UI_STC_LEXER)
        Subscribe(self.OnPageChange,EDMSG_UI_NB_CHANGED)
        
    
        
    def GetMenuHandlers(self):
        return [(ID_EDIT_TEMPLATES,self.OnEdit),
                (ID_SHOW_TEMPLATES,self.OnShow)]
    
    def GetUIHandlers(self):
        return []
            
    def OnShow(self, evt):
        if evt.GetId() == ID_SHOW_TEMPLATES:
            current_buffer = wx.GetApp().GetCurrentBuffer()
            lst = self.templates[self.currentlang].keys()
            #lst = self.templates[current_buffer.GetLangId()].keys()
            lst.sort()
            wx.GetApp().GetCurrentBuffer().UserListShow(1, u' '.join(lst))
        else:
            evt.skip()
        
    #def OnTemplate(self,evt): #from before when binding directly to event
    def OnTemplate(self,msg):
        current_buffer = wx.GetApp().GetCurrentBuffer()
        #text = evt.GetText()
        text = msg.GetData()['text']
        self.templates[self.currentlang][text].DoTemplate(current_buffer)
        #self.templates[current_buffer.GetLangId()][text].DoTemplate(current_buffer)
        
    def OnLexerChange(self,msg):
        fn,ftype = msg.GetData()
        if Profile_Get(PROFILE_KEY_FOLLOW_LANG):
            self._log("[codetemplater][info] changing to language %s for file %s due to lexer change"%(ftype,fn))
            self.currentlang = ftype
    
    def OnPageChange(self,msg):
        current_buffer = wx.GetApp().GetCurrentBuffer()
        if Profile_Get(PROFILE_KEY_FOLLOW_LANG):
            lid = current_buffer.GetLangId()
            self._log("[codetemplater][info] changing to language %s due to page change"%lid)
            self.currentlang = lid
            
    def OnEdit(self, evt):
        if evt.GetId() == ID_EDIT_TEMPLATES:
            self._log("[codetemplater][info] Loading Editor Dialog")
            
            current_buffer = wx.GetApp().GetCurrentBuffer()
            
            ilang = self.currentlang
            #ilang = current_buffer.GetLangId()
            
            dlg = TemplateEditorDialog(self.mw,self,-1,_('Code Template Editor'),initiallang=ilang)
            
            dlg.ShowModal()
            dlg.edpanel.ApplyTemplateInfo()
            dlg.Destroy()
            self._log("[codetemplater][info] Completed Editing")
        else:
            evt.Skip()
            
#    def AddTemplate(self,templateobj):
#        """
#        if template is already present, it will be overwritten
#        """
#        self.templates[templateobj.name] = templateobj
#    def RemoveTemplate(self,templateobjorkey):
#        if isinstance(templateobjorkey,basestring):
#            delk = templateobjorkey
#        else:
#            delk = None
#            for k,v in self.templates.iteritems():
#                if v is templateobjorkey:
#                    delk = k
#                    break
#            if delk is None:
#                raise KeyError('template '+str(templateobjorkey)+' not found')
#        del self.templates[delk]

def GetConfigObject():
    return CodeTemplaterConfig()

