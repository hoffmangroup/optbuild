#!/usr/bin/env python

"""
disttest 0.1
by Michael Hoffman <hoffman@ebi.ac.uk>

Copyright 2003 Michael Hoffman
"""

__version__ = "$Revision: 1.2 $"

import distutils.command.build
import distutils.command.install
import distutils.core
import distutils.util
from distutils.util import get_platform
import doctest
from glob import glob
import imp
import itertools
import fnmatch
import os
import pdb
import sys
import unittest

TEST_DIR = "test"
TEST_GLOB = os.path.join(TEST_DIR, "test_*.py")
ALL_GLOB = "*.py"

class PostMortemTextTestResult(unittest._TextTestResult):
    def addFailure(self, test, err):
        unittest._TextTestResult.addFailure(self, test, err)
        self.post_mortem("FAIL", test, err)

    def addError(self, test, err):
        unittest._TextTestResult.addError(self, test, err)
        self.post_mortem("ERROR", test, err)

    def post_mortem(self, flavor, test, err):
        self.print_error(flavor, test, err)

        (exctype, excvalue, traceback) = err
        pdb.post_mortem(traceback)

    def print_error(self, flavor, test, err):
        self.stream.writeln(self.separator1)
        self.stream.writeln("%s: %s" % (flavor, self.getDescription(test)))
        self.stream.writeln(self.separator2)
        self.stream.writeln("%s" % self._exc_info_to_string(err, test))

class PostMortemTextTestRunner(unittest.TextTestRunner):
    def _makeResult(self):
        return PostMortemTextTestResult(self.stream, self.descriptions,
                                        self.verbosity)

class test(distutils.command.build.build):
    description = "run the test suite"

    # XXX: set more specific user_options

    user_options = [
        ('build-base=', 'b',
         "base directory for build library"),
        ('build-purelib=', None,
         "build directory for platform-neutral distributions"),
        ('build-platlib=', None,
         "build directory for platform-specific distributions"),
        ('build-lib=', None,
         "build directory for all distribution (defaults to either " +
         "build-purelib or build-platlib"),
        ("post-mortem", None,
         "enter debugger on failure or error"),
        ('skip-build', None,
         "skip rebuilding everything (for testing/debugging)")]
    help_options = []
    boolean_options = ['post-mortem', 'skip-build']

    def initialize_options(self):
        self.post_mortem = False
        self.skip_build = False

        self.build_base = 'build'
        # these are decided only after 'build_base' has its final value
        # (unless overridden by the user or client)
        self.build_purelib = None
        self.build_platlib = None
        self.build_lib = None

    def finalize_options (self):
        # copied from distutils.command.build.build

        plat_specifier = ".%s-%s" % (get_platform(), sys.version[0:3])

        # 'build_purelib' and 'build_platlib' just default to 'lib' and
        # 'lib.<plat>' under the base build directory.  We only use one of
        # them for a given distribution, though --
        if self.build_purelib is None:
            self.build_purelib = os.path.join(self.build_base, 'lib')
        if self.build_platlib is None:
            self.build_platlib = os.path.join(self.build_base,
                                              'lib' + plat_specifier)

        # 'build_lib' is the actual directory that we will use for this
        # particular module distribution -- if user didn't supply it, pick
        # one of 'build_purelib' or 'build_platlib'.
        if self.build_lib is None:
            if self.distribution.ext_modules:
                self.build_lib = self.build_platlib
            else:
                self.build_lib = self.build_purelib

    def run(self):
        if not self.skip_build:
            self.run_command('build')

        sys.path.insert(0, self.build_lib)
        all_tests = unittest.TestSuite()

        # XXX: break these out as sub_commands
        all_tests.addTests(self.tests_unittest())
        all_tests.addTests(self.tests_doctest())

        if "-v" in sys.argv or "--verbose" in sys.argv:
            verbosity=2
        else:
            verbosity=0

        if self.post_mortem:
            test_runner = PostMortemTextTestRunner
        else:
            test_runner = unittest.TextTestRunner

        test_runner(verbosity=verbosity).run(all_tests)

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

# XXX: touch a file if testing is done so you don't test over and over
class install(distutils.command.install.install):
    user_options = distutils.command.install.install.user_options + \
                   [('skip-test', None, "skip testing")]

    def initialize_options(self):
        self.skip_test = False
        return distutils.command.install.install.initialize_options(self)

    def run(self):
        if not self.skip_test:
            self.run_command('test')

        return distutils.command.install.install.run(self)

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
