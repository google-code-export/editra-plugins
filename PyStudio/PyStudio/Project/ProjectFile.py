###############################################################################
# Name: ProjectFile.py                                                        #
# Purpose: Project File Abstraction                                           #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2011 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################

"""
ProjectFile

Project Data class representing the Project file

@see: ProjectXml

"""

#-----------------------------------------------------------------------------#
# Imports
import os

# Editra imports
import ed_msg
import ebmlib

# Local Imports
import PyStudio.Project.ProjectXml as ProjectXml
from PyStudio.Common.Messages import PyStudioMessages

#-----------------------------------------------------------------------------#

class ProjectFile(object):
    """Project file for use by the ProjectMgr"""
    def __init__(self, pxml, path):
        """
        @param pxml: ProjectXml
        @param path: Xml file path

        """
        super(ProjectFile, self).__init__()

        # Attributes
        self._pxml = pxml  # Project file xml data (serialization)
        self._path = path  # Project file path
        self._dirty = False
        # Derived attributes
        self._optmap = dict() # Project option map

        # Setup
        self.__RefreshOptionMap()

    def __RefreshOptionMap(self):
        """Build the option map"""
        self._optmap.clear()
        for opt in self._pxml.options:
            self._optmap[opt.name] = opt

    #---- Properties ----#

    Path = property(lambda self: self._path)
    ProjectRoot = property(lambda self: os.path.dirname(self.Path))
    ProjectName = property(lambda self: self._pxml.name)
    Dirty = property(lambda self: self._dirty)

    #---- Implementation ---- #

    def Save(self):
        """Save the project file to disk"""
        if self.Dirty:
            self._pxml.Write(self.Path)
            self._dirty = False
            # Post notification for any observers that project settings have
            # been saved to disk.
            ed_msg.PostMessage(PyStudioMessages.PYSTUDIO_PROJECT_SAVED, self)

    #---- Project Data Accessors ----#

    def GetOption(self, optname):
        """Get the value for a project option
        @param optname: option name
        @return: option value or None

        """
        option = self._optmap.get(optname, None)
        if option:
            option = option.value
        return option

    def SetOption(self, optname, value):
        """Set a project option
        @param optname: option name
        @param value: option value

        """
        if optname in self._optmap:
            if self._optmap[optname].value != value:
                self._optmap[optname].value = value
                self._dirty = True
        else:
            # New option
            nopt = ProjectXml.Option(name=optname, value=value)
            self._pxml.options.append(nopt)
            self.__RefreshOptionMap()
            self._dirty = True
        if self.Dirty:
            ed_msg.PostMessage(PyStudioMessages.PYSTUDIO_PROJECT_MODIFIED,
                               dict(project=self, option=optname))

    #---- Project File Accessors ----#

    def GetAllProjectFiles(self):
        """Get all the source files in the project.
        @return: ebmlib.Directory

        """
        return ebmlib.GetDirectoryObject(self.ProjectRoot)
