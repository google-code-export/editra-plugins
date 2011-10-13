###############################################################################
# Name: ProjectTemplate.py                                                    #
# Purpose: Project Templates                                                  #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2011 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################

"""
ProjectTemplate

Data class for defining project templates

"""

xml_str = """
<template id='FooBar'>
    <file name="__init__.py"/>
    <file name="LICENCE">
        <data>Test data field</data>
    </file>
    <dir name="src">
        <file name="test.py"/>
    </dir>
</template>
"""

__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports

# Editra Imports
#import sys
#sys.path.append(r"..\..\..\..\..\src") # TEST
import ed_xml

#-----------------------------------------------------------------------------#
# Special keys for xml attribute values

# Automatically insert project name
PROJECT_NAME = u"%(projName)s"

#-----------------------------------------------------------------------------#

class ProjectTemplate(ed_xml.EdXml):
    """Project template XML
    The template id is used as the template name for user defined templates
    and as an internal identifier for the default provided ones.

    <template id='TemplateID'>
    </template>

    """
    class meta:
        tagname = "template"
    id = ed_xml.String(required=True)
    # Optional default files and directories
    files = ed_xml.List(ed_xml.Model("file"), required=False)
    dirs = ed_xml.List(ed_xml.Model("dir"), required=False)

class TemplateCollection(ed_xml.EdXml):
    """List of ProjectTemplates
    <projectTemplates>
        <template projName='Foo'>
            ...
        <template projName='Bar'>
            ...
    </projectTemplates>

    """
    class meta:
        tagname = "projectTemplates"
    templates = ed_xml.List(ed_xml.Model(type=ProjectTemplate))

    def FindTemplate(self, name):
        """Find a template based on the given name
        @param name: string
        @return: ProjectTemplateXml or None

        """
        for t in self.templates:
            if t.name == name:
                return t
        return None

#---- Subelements of a template ----#

class File(ed_xml.EdXml):
    """Xml element to represent a file item
    <file name='__init__.py'>
        # File: __init__.py
        ''' docstring '''
    </file>

    """
    class meta:
        tagname = "file"
    name = ed_xml.String(required=True)
    data = ed_xml.String(tagname="data", required=False) # optional specify initial file contents

class Directory(ed_xml.EdXml):
    """Xml element to represent a directory item
    <dir name='src'>
        <file ...>
        <file ...>
    </dir>

    """
    class meta:
        tagname = "dir"
    name = ed_xml.String(required=True)
    files = ed_xml.List(ed_xml.Model(type=File), required=False)
    dirs = ed_xml.List(ed_xml.Model("dir"), required=False)

#-----------------------------------------------------------------------------#

def GetDefaultTemplates():
    """Get the TemplateCollection of default project recipes
    @return: TemplateCollection

    """
    plist = TemplateCollection()
    ## Empty Project
    empty = ProjectTemplate(id=u"__EMPTY__")
    plist.templates.append(empty)

    ## Basic project
    simple = ProjectTemplate(id=u"__BASIC__")
    for fname in ('CHANGELOG', 'README', 'setup.py', 'LICENSE'):
        simple.files.append(File(name=fname))
    sdir = Directory(name=PROJECT_NAME)
    sdir.files.append(File(name="__init__.py"))
    simple.dirs.append(sdir)
    plist.templates.append(simple)

    return plist

def MapDisplayName(templateId):
    """Get the display name for the given template ID
    @return: unicode or None

    """
    name_map = { u"__EMPTY__" : _("Empty Project"),
                 u"__BASIC__" : _("Basic Project") }
    return name_map.get(templateId, None)

#-----------------------------------------------------------------------------#


#-----------------------------------------------------------------------------#

if __name__ == '__main__':
    pto = ProjectTemplate.LoadString(xml_str)
    for f in pto.files:
        print f.name, repr(f.data)
    print GetDefaultTemplates().PrettyXml
