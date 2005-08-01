#!/usr/bin/env python

__version__ = "$Revision: 1.2 $"

import sys
import unittest

import optbuild

# XXX: look at tests from test_subprocess as inspiration

class TestOptionBuilder(unittest.TestCase):
    def setUp(self):
        self.ob = optbuild.OptionBuilder(prog="myprogram")
    
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
        self.assertEqual(self.ob.build_args(["file1", "file2"],
                                            dict(moocow="milk")),
                         ["--moocow=milk", "file1", "file2"])
        self.assertEqual(self.ob.build_args(args=["file1"]), ["file1"])
        self.assertEqual(self.ob.build_args(["file1"], {"this": True,
                                             "is": None,
                                             "it": 42}),
                         ["--this", "--it=42", "file1"])

    def test_build_cmdline(self):
        self.assertEqual(self.ob.build_cmdline(["/usr/local"],
                                               dict(color=True),
                                               "ls"),
                         ["ls", "--color", "/usr/local"])
        self.assertEqual(self.ob.build_cmdline(args=["infile", "outfile"]),
                         ["myprogram", "infile", "outfile"])

    def test_run(self):
        self.ob.prog = "ls"
        self.assertEqual(self.ob.run("/usr/local", color=True), None)

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
        except optbuild.SignalError, err:
            self.assert_(str(err).endswith("terminated by SIGKILL"))

class TestReturncodeError(TestPythonSubprocess):
    command = "import sys; sys.exit(33)"

    def test_being_raised(self):
        self.assertRaises(optbuild.ReturncodeError, self.run_python)

if __name__ == "__main__":
    unittest.main()
