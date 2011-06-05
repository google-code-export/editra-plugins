# Setup script for building the Projects egg

from setuptools import setup

__author__ = "Kevin D. Smith <Kevin.Smith@sixquickrun.com>"
__revision__ = "$Revision$"
__scid__ = "$Id$"
__doc__ = "Projects"
__version__ = "1.8"

setup(
      name    = "Projects",
      version = __version__,
      description = __doc__,
      author = "Kevin D. Smith",
      author_email = "Kevin.Smith@theMorgue.org",
      maintainer = "Cody Precord",
      maintainer_email = "cprecord@editra.org",
      license = "wxWindows",
      package_data={'projects' : ['locale/*/LC_MESSAGES/*.mo']},
      packages = ['projects'],
      entry_points = '''
      [Editra.plugins]
      Projects = projects:Projects
      ModList = projects:ProjectsModList
      ''',
     )
