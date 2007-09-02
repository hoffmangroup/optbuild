#!/usr/bin/env python

"""optbuild: build command lines for external programs

like optparse but in reverse
"""

__version__ = "0.1.1"

from setuptools import setup

doclines = __doc__.splitlines()
name, short_description = doclines[0].split(": ")
long_description = "\n".join(doclines[2:])

setup(name=name,
      version=__version__,
      description=short_description,
      author="Michael Hoffman",
      author_email="hoffman+optbuild@ebi.ac.uk",
      url="http://www.ebi.ac.uk/~hoffman/software/",
      license="GNU GPL",
      long_description=long_description,
      package_dir={'': 'lib'},
      py_modules=['optbuild'],
      requires=['autolog'],
      install_requires=['autolog'],
      zip_safe=True
      )
