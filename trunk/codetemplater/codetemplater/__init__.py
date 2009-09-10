#from __future__ import with_statement #avoiding with statement for 2.4 compatibility
"""Applies Code Templates for regularly-used design patterns."""
__author__ = "Erik Tollerud"
__version__ = "0.1"

import wx                   
import iface
import plugin
from os import path
from ed_glob import CONFIG,SB_INFO,ID_RELOAD_ENC
from ed_menu import EdMenu
from profiler import Profile_Get, Profile_Set
trans = wx.GetTranslation

from string import Template

ID_EDIT_TEMPLATES  = wx.NewId()
ID_SEP_TEMPLATES = None #set when seperator is created
ID_SAVE_TO_PROF = wx.NewId()

PROFILE_KEY_TEMPLATES = 'CodeTemplater.Templates'
 
class CodeTemplater(plugin.Plugin):
    """Adds a Save/Load Session Menu Item to the MainWindow File Menu"""
    plugin.Implements(iface.MainWindowI)  
    
    def __init__(self,*args,**kwargs):
        plugin.Plugin.__init__(self,*args,**kwargs)
        self.templates = dict()
        self.loadDefaultTemplates()
    
    def PlugIt(self, parent):
        """Implements MainWindowI's PlugIt Method"""
        self.mw = parent
        self._log = wx.GetApp().GetLog()
        self._log("[CodeTemplater][info] Starting codetemplater")
        
        self.templatemenu = submenu = EdMenu()
        
        #add default-loaded templates
        for id,(name,temp,help,obeyindent) in self.templates.iteritems():
            item = wx.MenuItem(submenu,id,trans(name),trans(help))
            submenu.AppendItem(item)
            
        global ID_SEP_TEMPLATES
        ID_SEP_TEMPLATES = submenu.AppendSeparator().GetId()
        submenu.Append(ID_EDIT_TEMPLATES,trans('Edit Templates...'),
                 trans('Open a Dialog to Edit the Templates Currently in Use'))
                       
        toolmenu = self.mw.GetMenuBar().GetMenuByName("tools")
        toolmenu.AppendSubMenu(submenu,'Code Templates',trans('Insert Code Templates into Document'))
 
    def GetMenuHandlers(self):
        hands = [(ID_EDIT_TEMPLATES,self.OnEdit)]
        hands.extend([(id, self.OnTemplate) for id in self.templates]) #any default templates get added here
        return hands
    
    def GetUIHandlers(self):
        return []
        
    def AddCodeTemplate(self,name,templatestr,help=u'',obeyindent=True):
        """
        Note that this will overwrite any existing template with the same name.
        
        This should only be used AFTER initialization (it adds new MenuHandlers)
        """
        temp = Template(templatestr)
        nms = [v[0] for v in self.templates.values()]
        
        if name in nms:
            i = nms.index(name)
            oldentry = self.templates.values()[i]
            newentry = (name,temp,help if help is not u'' else oldentry[2],obeyindent)
            self._log("[CodeTemplater][info] Updating Code Template "+str(name))
            self.templates[self.templates.keys()[i]] = newentry
        else:
            self._log("[CodeTemplater][info] Adding entry for Code Template "+str(name))
            
            entry = (name,temp,help,obeyindent)
            newid = wx.NewId()
            self._addTemplateToMenu(newid,entry)            
            #add templates entry only after all wx stuff definitely worked
            self.templates[newid] = entry
            
    def _addTemplateToMenu(self,id,entry):
        name,temp,help,obeyindent = entry
        
        if self.templatemenu.GetMenuItemCount() < 3:
            self.templatemenu.Insert(0,id,trans(name),trans(help))
        else:
            self.templatemenu.InsertBefore(ID_SEP_TEMPLATES,id,trans(name),trans(help))
        
        handler = (id,self.OnTemplate)
        #TODO:ensure this isn't dangerous
        self.mw.AddMenuHandler(*handler)
        wx.GetApp().AddHandlerForID(*handler) 
            
    def RemoveCodeTemplate(self,idorname):
        """
        does nothing if idorname is not present 
        """
        if isinstance(idorname,int):
            id = idorname
            if id not in self.templates:
                return
        elif isinstance(idorname,basestring):
            try:
                nms = [v[0] for v in self.templates.values()]
                id = self.templates.keys()[nms.index(idorname)]
            except ValueError:
                return
        else:
            return 
        
        assert id in self.templates,'id missing from templates dict'
        
        #name,temp,help,obeyindent = self.templates[id] 
        item = self.templatemenu.FindItemById(id)
        self.templatemenu.Remove(id)
        if item is not None:
            item.Destroy()
        del self.templates[id] 
        
            
    def loadDefaultTemplates(self,checkprofile=True):
        if checkprofile and (Profile_Get(PROFILE_KEY_TEMPLATES) is not None):
            for entry in Profile_Get(PROFILE_KEY_TEMPLATES):
                id = wx.NewId()
                self.templates[id] = entry
        else:
            #self.templates: {id:(namestr,template,helpstr,obeyindentbool)}
            proptemp = Template("""
def _get${upper}(self):
    #CUR
def _set${upper}(self,val):
    raise NotImplementedError
${same} = property(_get${upper},_set${upper},doc=None)
"""[1:]) #remove first EOL
            id = wx.NewId()
            self.templates[id] = ('Property',proptemp,trans('Convert Selection to Get/Set Property'),True)
            
            delproptemp = Template("""
def _get${upper}(self):
    #CUR
def _set${upper}(self,val):
    raise NotImplementedError
def _del${upper}(self):
    raise NotImplementedError
${same} = property(_get${upper},_set${upper},_del${upper},doc=None)
"""[1:]) #remove first EOL
            id = wx.NewId()
            self.templates[id] = ('DelProperty',delproptemp,trans('Convert Selection to Get/Set/Del Property'),True)
            
            getproptemp = Template("""
@property
def ${same}(self):
    #CUR
"""[1:]) #remove first EOL
            id = wx.NewId()
            self.templates[id] = ('ROProperty',getproptemp,trans('Convert Selection to read-only Property'),True)
            
            iteritemstemp = Template("""
for k,v in ${same}.iteritems():
    #CUR
"""[1:]) #remove first EOL
            id = wx.NewId()
            self.templates[id] = ('Iterdict',iteritemstemp,trans('Iterate over items of selected dictionary'),True)
            
            methodtemp = Template("""
def ${same}(self):
    #CUR
"""[1:]) #remove first EOL
            id = wx.NewId()
            self.templates[id] = ('Method',methodtemp,trans('Convert selection into a method'),True)
            
            nietemp = Template('raise NotImplementedError')
            id = wx.NewId()
            self.templates[id] = ('NotImplementedError',nietemp,u'',True)

            
    def OnTemplate(self, evt):
        id= evt.GetId()
        if id in self.templates:
            name,temp,help,indent = self.templates[id]
            
            page = self.mw.GetNotebook().GetCurrentPage()
            seltext = page.GetSelectedText().strip()
            
            submap = {}
            seltext.strip()
            submap['same'] = seltext
            if len(seltext) > 0:
                submap['upper'] = seltext[0].upper()+seltext[1:]
                submap['lower'] = seltext[0].lower()+seltext[1:]
            else:
                submap['upper'] = submap['lower'] = seltext
            self._log("[CodeTemplater][info] Applying template %s to %s"%(name,submap['same']))
            
            if indent:
                #compute indentation
                line = page.GetCurrentLine()
                indentcount = page.GetLineIndentation(line)/page.GetTabWidth()
                indentstr = page.GetIndentChar()*indentcount
            else:
                indentstr = u''
                
            page.DeleteBack()
            propstring = temp.safe_substitute(submap)
            fullstring = propstring.replace('\n',page.GetEOLChar()+indentstr)
            if '#CUR' in fullstring:
                curind = fullstring.index('#CUR')
                curoffset = len(fullstring)-4-curind
                fullstring = fullstring.replace('#CUR','',1)
            else:
                curoffset = None
            page.AddText(fullstring)
            if curoffset is not None:
                newpos = page.GetCurrentPos()-curoffset
                page.SetCurrentPos(newpos)
                page.SetSelection(newpos,newpos)
        else:
            evt.Skip()
            
    def OnEdit(self, evt):
        if evt.GetId() == ID_EDIT_TEMPLATES:
            self._log("[CodeTemplater][info] Loading Editor Dialog")
            
            dlg = TemplateEditorDialog(self.mw,self,-1,trans('Code Template Editor'))
            
            dlg.ShowModal()
            dlg.edpanel.applyTemplateInfo()
            dlg.Destroy()
            self._log("[CodeTemplater][info] Completed Editing")
        else:
            evt.Skip()
    
    def saveToProfile(self,reset=False):
        Profile_Set(PROFILE_KEY_TEMPLATES,None if reset else self.templates.values())

class TemplateEditorDialog(wx.Dialog):
    def __init__(self, parent, plugin, ID, title, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.DEFAULT_DIALOG_STYLE):
            
        #pre = wx.PreDialog()
        #pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        #pre.Create(parent, ID, title, pos, size, style)
        #self.PostCreate(pre)
        wx.Dialog.__init__(self, parent, ID, title, pos, size, style)
        
        basesizer = wx.BoxSizer(wx.VERTICAL)
        
        self.edpanel = TemplateEditorPanel(self,plugin,-1)
        basesizer.Add(self.edpanel,0)
        
        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        basesizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)
        
        btnsizer = wx.BoxSizer(wx.HORIZONTAL)
        okbtn = wx.Button(self, wx.ID_OK)
        okbtn.SetDefault()
        btnsizer.Add(okbtn, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        profbtn = wx.Button(self, ID_SAVE_TO_PROF,trans('Save to Profile'))
        profbtn.SetToolTipString(trans('Save to the Profile to be reloaded on next Startup'))
        profbtn.Bind(wx.EVT_BUTTON, self.OnSaveProfile)
        btnsizer.Add(profbtn, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        resetbtn = wx.Button(self, ID_SAVE_TO_PROF,trans('Reset to defaults'))
        resetbtn.SetToolTipString(trans('Resets the Profile to default as well as the Current Setup'))
        resetbtn.Bind(wx.EVT_BUTTON, self.OnResetProfile)
        btnsizer.Add(resetbtn, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        basesizer.Add(btnsizer,0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL)

        self.SetSizer(basesizer)
        basesizer.Fit(self)
        
    def OnSaveProfile(self,evt):
        self.edpanel.applyTemplateInfo()
        self.edpanel.plugin.saveToProfile()
    
    def OnResetProfile(self,evt):
        pa = self.edpanel
        plug = pa.plugin
        
        #clear out the current templates and then reset the profile to None
        pa.updateTemplateinfoUI(None)
        for id in plug.templates.keys():
            plug.RemoveCodeTemplate(id)
        
        #now add back in the defaults
        plug.loadDefaultTemplates(checkprofile=False)
        for id,entry in plug.templates.iteritems():
            plug._addTemplateToMenu(id,entry) 
        pa.listbox.SetItems(pa.getTemplateIDNames()[1])
        
        
class TemplateEditorPanel(wx.Panel):
    def __init__(self,parent,plugin, *args, **kwargs):
        wx.Panel.__init__(self,parent, *args, **kwargs)
        self.plugin = plugin
        self.removing = False
        self.lastind = None
        
        basesizer = wx.BoxSizer(wx.HORIZONTAL)
        
        #left side of panel to display and alter list of templates
        listsizer = wx.BoxSizer(wx.VERTICAL)
        
        label = wx.StaticText(self, -1, trans("Code Templates"))
        listsizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        self.listbox = wx.ListBox(self, -1,size=(150,300), choices=self.getTemplateIDNames()[1], style=wx.LB_SINGLE)
        self.Bind(wx.EVT_LISTBOX, self.OnListChange, self.listbox)
        listsizer.Add(self.listbox, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        buttonsizer = wx.BoxSizer(wx.HORIZONTAL)
        addbutton = wx.Button(self,wx.ID_ADD)
        addbutton.SetToolTipString(trans('Add a New Template'))
        self.Bind(wx.EVT_BUTTON, self.OnAdd, addbutton)
        buttonsizer.Add(addbutton,1,wx.ALIGN_CENTRE|wx.ALL, 5)
        rembutton = wx.Button(self,wx.ID_DELETE)
        rembutton.SetToolTipString(trans('Remove the selected Template'))
        self.Bind(wx.EVT_BUTTON, self.OnRemove, rembutton)
        buttonsizer.Add(rembutton,1,wx.ALIGN_CENTRE|wx.ALL, 5)
        listsizer.Add(buttonsizer, 0, wx.ALIGN_CENTRE|wx.ALL, 2)
        
        basesizer.Add(listsizer, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        
        
        #right side of panel to display the selected template
        templateinfo = wx.BoxSizer(wx.VERTICAL)
        
        namesizer = wx.BoxSizer(wx.HORIZONTAL)
        helplabel = wx.StaticText(self, -1, trans("Name:"))
        namesizer.Add(helplabel,0,wx.ALIGN_CENTRE|wx.ALL, 2)
        self.nametxt = wx.TextCtrl(self,-1)
        namesizer.Add(self.nametxt,1,wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 2)
        templateinfo.Add(namesizer, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 2)
        
        helpsizer = wx.BoxSizer(wx.HORIZONTAL)
        helplabel = wx.StaticText(self, -1, trans("Help Text:"))
        helpsizer.Add(helplabel,0,wx.ALIGN_CENTRE|wx.ALL, 2)
        self.helptxt = wx.TextCtrl(self,-1)
        helpsizer.Add(self.helptxt,1,wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 2)
        templateinfo.Add(helpsizer, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 2)
        
        indsizer = wx.BoxSizer(wx.HORIZONTAL)
        indlabel = wx.StaticText(self, -1, trans("Obey Indentation?"))
        indsizer.Add(indlabel,0,wx.ALIGN_CENTER|wx.ALL, 2)
        self.indentcb = wx.CheckBox(self)
        indsizer.Add(self.indentcb,0,wx.ALIGN_CENTRE|wx.ALL, 2)
        templateinfo.Add(indsizer, 0, wx.ALIGN_CENTER|wx.ALL, 2)
        
        templabel = wx.StaticText(self, -1, trans('Template Codes:\n')+
                '"${same}": '+trans('Replace with selected text.\n"')+
                '${upper}":'+trans('Replace with selected, first character upper case.\n')+
                '"${lower}":'+trans('Replace with selected, first character lower case.\n')+
                '"$$":'+trans('An "$" character.')+'\n'+
                '"#CUR":'+trans('Move cursor to this location after inserting template.'))
        templateinfo.Add(templabel, 0, wx.ALIGN_CENTER|wx.ALL, 2)
        self.temptxt = wx.TextCtrl(self,-1,size=(400,300),style = wx.TE_MULTILINE)
        templateinfo.Add(self.temptxt, 1, wx.GROW|wx.ALL, 2)
        
        basesizer.Add(templateinfo, 1, wx.GROW|wx.ALIGN_CENTER|wx.ALL, 5)
        
        self.SetSizer(basesizer)
        basesizer.Fit(self)
        
    def getTemplateIDNames(self):
        ids = self.plugin.templates.keys()
        nms = [t[0] for t in self.plugin.templates.values()]
        return ids,nms
    
    def updateTemplateinfoUI(self,name):
        ids,nms = self.getTemplateIDNames()
        try:
            id = ids[nms.index(name)]
        except ValueError:
            id = None
            
        if id is None:
            #starts out blank
            self.nametxt.SetValue(str(name) if name is not None else '')
            self.temptxt.SetValue('')
            self.helptxt.SetValue('')
            self.indentcb.SetValue(False)
        else:
            name,temp,help,obeyindent = self.plugin.templates[id] 
            tempstr = temp.template
            self.nametxt.SetValue(name)
            self.temptxt.SetValue(tempstr)
            self.helptxt.SetValue(help)
            self.indentcb.SetValue(obeyindent)
            
    def applyTemplateInfo(self,updatelistind=None):
        name = self.nametxt.GetValue()
        if name.startswith('<') or name.endswith('>') or name.strip()=='':
            return #don't apply initial names
        
        help = self.helptxt.GetValue()
        tempstr = self.temptxt.GetValue()
        obeyind = self.indentcb.GetValue()
        
        self.plugin.AddCodeTemplate(name,tempstr,help,obeyind)
        if updatelistind is not None:
            self.listbox.SetString(updatelistind,name)
        
            
    def OnAdd(self,evt):
        items = self.listbox.Append('<'+trans('New Template')+'>')
    
    def OnRemove(self,evt):
        self.removing = True
        name = self.listbox.GetStringSelection()
        self.listbox.Delete(self.listbox.GetSelection())
        self.plugin.RemoveCodeTemplate(name) #does nothing if not present
        self.lastind = None
        self.updateTemplateinfoUI(None)
        self.removing = False
        
    def OnListChange(self,evt):
        if not self.removing:
            self.applyTemplateInfo(updatelistind=self.lastind)
        self.updateTemplateinfoUI(evt.GetString())
        self.lastind = evt.GetSelection()
            
#TODO: config panel -- need to figure out how to hand the panel the plugin object properly
#def GetConfigObject():
#    return CodeTemplaterConfig()
# 
#class CodeTemplaterConfig(plugin.PluginConfigObject):
#    """Plugin configuration object."""
#    def GetConfigPanel(self, parent):
#        """Get the configuration panel for this plugin
#        @param parent: parent window for the panel
#        @return: wxPanel
 
#        """
#        return TemplateEditorPanel(parent,plugin)
 
#    def GetLabel(self):
#        """Get the label for this config panel
#        @return string
 
#        """
#        return trans('Code Templater')
 

