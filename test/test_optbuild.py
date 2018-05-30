#!/usr/bin/env python

from __future__ import absolute_import
__version__ = "$Revision: 1.4 $"

import sys
import unittest

import optbuild

# XXX: look at tests from test_subprocess as inspiration

class TestOptionBuilder(unittest.TestCase):
    def setUp(self):
        # not really a GNU option builder, but it's the only executable we know
        # about for sure
        self.ob = optbuild.OptionBuilder(prog=sys.executable)

    def test_convert_option_name(self):
        self.assertEqual(self.ob.convert_option_name("long_name"), "long-name")
        self.assertEqual(self.ob.convert_option_name("long-name"), "long-name")

    def test_build_option(self):
        self.assertEqual(self.ob._build_option("long_name", "foo"),
                         ["--long-name=foo"])
        self.assertEqual(self.ob.build_option("number", 42), ["--number=42"])
        self.assertEqual(self.ob.build_option("boolean", True), ["--boolean"])
        self.assertEqual(self.ob.build_option("boolean2", False), [])
        self.assertEqual(self.ob.build_option("long_name2", None), [])

    def test_build_args(self):
        built = self.ob.build_args(["file1", "file2"], dict(moocow="milk"))
        self.assertEqual(built, ["--moocow=milk", "file1", "file2"])

        built = self.ob.build_args(args=["file1"])
        self.assertEqual(built, ["file1"])

        built = self.ob.build_args(["file1"],
                                   {"this": True, "is": None, "it": 42})
        self.assertEqual(built, ["--it=42", "--this", "file1"])


    def test_build_cmdline(self):
        built = self.ob.build_cmdline(["/usr/local"], dict(color=True), "ls")
        self.assertEqual(built, ["ls", "--color", "/usr/local"])

        built = self.ob.build_cmdline(args=["infile", "outfile"])
        self.assertEqual(built, [sys.executable, "infile", "outfile"])

    def test_run(self):
        self.assertEqual(self.ob.run("-c", "pass"), None)

class TestPythonSubprocess(unittest.TestCase):
    def setUp(self):
        self.ob = optbuild.OptionBuilder_ShortOptWithSpace(prog=sys.executable)

    def run_python(self):
        return self.ob.run(c=self.command)

class TestSignalError(TestPythonSubprocess):
    command = "import os; os.kill(os.getpid(), 9)"

    def test_being_raised(self):
        self.assertRaises(optbuild.SignalError, self.run_python)

    def test_str(self):
        try:
            self.run_python()
        except optbuild.SignalError as err:
            self.assertTrue(str(err).endswith("terminated by SIGKILL"))

class TestReturncodeError(TestPythonSubprocess):
    command = "import sys; sys.exit(33)"

    def test_being_raised(self):
        self.assertRaises(optbuild.ReturncodeError, self.run_python)

if __name__ == "__main__":
    unittest.main()
