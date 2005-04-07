#!/usr/bin/env python

"""
disttest 0.1
by Michael Hoffman <hoffman@ebi.ac.uk>

Copyright 2003 Michael Hoffman
"""

__version__ = "$Revision: 1.1.1.1 $"

import distutils.core
import distutils.util
import distutils.command.build
import doctest
from glob import glob
import imp
import itertools
import fnmatch
import os
import sys
import unittest

TEST_DIR = "test"
TEST_GLOB = os.path.join(TEST_DIR, "test_*.py")
ALL_GLOB = "*.py"

class disttest(distutils.command.build.build):
    description = "run the test suite"

    # XXX: set more specific user_options

    def run(self):
        # XXX: if not self.skip_build (from install)
        self.run_command('build')
        
        sys.path.insert(0, self.build_lib)
        all_tests = unittest.TestSuite()
        all_tests.addTests(self.tests_unittest())
        all_tests.addTests(self.tests_doctest())

        if "-v" in sys.argv or "--verbose" in sys.argv:
            verbosity=2
        else:
            verbosity=0

        unittest.TextTestRunner(verbosity=verbosity).run(all_tests)

    def tests_unittest(self):
        return [unittest.defaultTestLoader.loadTestsFromModule(module)
                for module in module_glob(TEST_GLOB)]

    def tests_doctest(self):
        res = []

        for module in module_walk(self.build_lib, ALL_GLOB):
            try:
                res.append(doctest.DocTestSuite(module))
            except AttributeError:
                return res
            except ValueError:
                pass

        return res

# XXX: touch a file if testing is done so you don't install over and over
#class install(distutils.command.install.install):
#    def run(self):
#        self.run_command('test')
#        super(install, self).run()

def walkall(top):
    for dirpath, dirnames, filenames in os.walk(top):
        for filename in filenames:
            yield os.path.join(dirpath, filename)

def walkglob(top, globspec):
    return fnmatch.filter(list(walkall(top)), globspec)

def load_modules(filenames):
    for filename in filenames:
        modulename = os.path.splitext(os.path.basename(filename))[0]
        try:
            import fixme
        except ImportError:
            class fixme(object):
                class Generic(object):
                    pass

        try:
            yield imp.load_source(modulename, filename, file(filename))
        except fixme.Generic:
            print "FIXME: %s" % fixme.filename()
            # don't yield; continue

def module_glob(globspec):
    return load_modules(glob(globspec))

def module_walk(top, globspec):
    return load_modules(walkglob(top, globspec))

def main():
    pass
    
if __name__ == "__main__":
    main()
