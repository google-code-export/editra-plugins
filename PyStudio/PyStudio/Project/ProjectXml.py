###############################################################################
# Name: ProjectXml.py                                                         #
# Purpose: Project Xml classes                                                #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2011 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################

"""
Project File

"""

# Test example xml
xml_str = """
<project name="FooBar">
    <option type="" value=""/>
    <package path="./foo/bar">
        <option type="" value=""/>
        <package path="./foo/bar/test">
            <option type="" value=""/>
        </package>
    </package>
    <folder path="/foo/bar">
        <option type="" value=""/>
    </folder>
</project>

"""

__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports
#import sys

# Editra Imports
#sys.path.append(r"C:\Users\n\Desktop\Editra\src") # TEST
import ed_xml

#-----------------------------------------------------------------------------#

class Option(ed_xml.EdXml):
    """General Option
    <option type="view" value="*.py"/>

    """
    class meta:
        tagname = "option"
    type = ed_xml.String(required=True)
    value = ed_xml.String(required=True)

class File(ed_xml.EdXml):
    """Xml element to represent a file item (used by ProjectTemplate)
    <file name='__init__.py'>
        # File: __init__.py
        ''' docstring '''
    </file>

    """
    class meta:
        tagname = "file"
    name = ed_xml.String(required=True)
    data = ed_xml.String(tagname="data", required=False) # optional specify initial file contents

class Folder(ed_xml.EdXml):
    """General folder container
    <folder path="/foo/test></folder>"

    """
    class meta:
        tagname = "folder"
    name = ed_xml.String(required=True)
    options = ed_xml.List(ed_xml.Model(type=Option), required=False)
    packages = ed_xml.List(ed_xml.Model("package"), required=False)
    folders = ed_xml.List(ed_xml.Model("folder"), required=False)
    files = ed_xml.List(ed_xml.Model(type=File), required=False)

class PyPackage(Folder):
    """Python package directory. Container for python modules."""
    class meta:
        tagname = "package"

class ProjectXml(Folder):
    """Main project structure"""
    class meta:
        tagname = "project"

    # Attributes
    name = ed_xml.String(required=True)

    # Child nodes
    folders = ed_xml.List(ed_xml.Model(type=Folder), required=False)
    packages = ed_xml.List(ed_xml.Model(type=PyPackage), required=False)
    options = ed_xml.List(ed_xml.Model(type=Option), required=False)

#-----------------------------------------------------------------------------#
# Test
if __name__ == '__main__':
    proj = ProjectXml()
    proj.name = "FooBar"
    pkg = PyPackage()
    pkg.path = "/foo/bar"
    opt = Option()
    opt.type = "wildcard"
    opt.value = "*.py"
    pkg.options.append(opt)
    proj.packages.append(pkg)
    tst = Folder()
    tst.path = r"C:\FooBar\test"
    proj.folders.append(tst)
    pp = Option()
    pp.type = "PYTHONPATH"
    pp.value = r"C:\Python26;C:\Desktop"
    proj.options.append(pp)
    print proj.PrettyXml
    print "------------------------"
    proj = ProjectXml.LoadString(xml_str)
    print proj.PrettyXml
