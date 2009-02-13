###############################################################################
# Name: testfinder.py
# Purpose: Unittest for pytools.finder
# Author: Rudi Pettazzi <rudi.pettazzi@gmail.com>
# Copyright: (c) 2009 Cody Precord <staff@editra.org>
# License: wxWindows License
###############################################################################

__author__ = "Rudi Pettazzi <rudi.pettazzi@gmail.com>"
__svnid__ = "$Id: Exp $"
__revision__ = "$Revision:  $"

#-----------------------------------------------------------------------------#
# Imports
import unittest
import StringIO
import os
import sys

sys.path.insert(0, os.path.abspath('../pytools'))

import finder

#-----------------------------------------------------------------------------#

class TestModuleFinder(unittest.TestCase):
    def setUp(self):
        self.finder = finder.ModuleFinder(finder.GetSearchPath())
        if sys.platform == 'win32':
            self.base = sys.prefix
        else:
            self.base = '%s/lib/python%s' % (sys.prefix, sys.version[:3])

    def tearDown(self):
        pass

    def testFind1(self):
        res = self.finder.Find('string')
        self.assertTrue(
            res.index(os.path.join(self.base, 'lib', 'string.py')) > -1 and
            res.index(os.path.join(self.base, 'lib', 'StringIO.py')) > -1)

    def testFind2(self):
        res = self.finder.Find('ctypes')
        self.check(res, [ os.path.join(self.base, 'lib', 'ctypes', '__init__.py') ])

    def testFind3(self):
        res = self.finder.Find('StringIO')
        self.check(res, [ os.path.join(self.base, 'lib', 'StringIO.py') ])

    def testFind4(self):
        self.assertEquals(self.finder.Find(''), [])

    def testFind5(self):
        self.assertEquals(self.finder.Find(None), [])

    def testFindUseImport(self):
        res = self.finder.Find('string', True)
        self.assertEquals(res[0], os.path.join(self.base, 'lib', 'string.py'))

    def check(self, lst1, lst2):
        lst1 = lst1.sort()
        lst2 = lst2.sort()
        self.assertEqual(lst1, lst2)

if __name__ == '__main__':
    unittest.main()



