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

# Local Imports
import PyStudio.Project.ProjectXml as ProjectXml

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
        self._pxml = pxml  # Project file xml data
        self._path = path  # Project file path
        # Derived attributes
        self._optmap = dict() # Project option map

        # Setup
        self.__RefreshOptionMap()

    def __RefreshOptionMap(self):
        """Build the option map"""
        for opt in self._pxml.options:
            self._optmap[opt.name] = opt

    #---- Properties ----#

    Path = property(lambda self: self._path)
    ProjectRoot = property(lambda self: os.path.dirname(self.Path))

    #---- Implementation ---- #

    def Save(self):
        """Save the project file to disk"""
        self._pxml.Write(self.Path)

    #---- Accessors ----#

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
            self._optmap[optname].value = value
        else:
            # New option
            nopt = ProjectXml.Option(name=optname, value=value)
            self._pxml.options.append(nopt)
            self.__RefreshOptionMap()
        