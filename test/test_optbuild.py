#!/usr/bin/env python

__version__ = "$Revision: 1.1.1.1 $"

import unittest

import optbuild

class TestOptionBuilder(unittest.TestCase):
    def setUp(self):
        self.ob = optbuild.OptionBuilder(prog="myprogram")
    
    def test_convert_option_name(self):
        self.assertEqual(self.ob.convert_option_name("long_name"), "long-name")
        self.assertEqual(self.ob.convert_option_name("long-name"), "long-name")

    def test_build_option(self):
        self.assertEqual(self.ob._build_option("long_name", "foo"), ["--long-name=foo"])
        self.assertEqual(self.ob.build_option("number", 42), ["--number=42"])
        self.assertEqual(self.ob.build_option("boolean", True), ["--boolean"])
        self.assertEqual(self.ob.build_option("boolean2", False), [])
        self.assertEqual(self.ob.build_option("long_name2", None), [])

    def test_build_args(self):
        self.assertEqual(self.ob.build_args(dict(moocow="milk"),
                                            ["file1", "file2"]),
                         ["--moocow=milk", "file1", "file2"])
        self.assertEqual(self.ob.build_args(args=["file1"]), ["file1"])
        self.assertEqual(self.ob.build_args({"this": True,
                                             "is": None,
                                             "it": 42}, ["file1"]),
                         ["--this", "--it=42", "file1"])

    def test_build_cmdline(self):
        self.assertEqual(self.ob.build_cmdline(dict(color=True), ["/usr/local"], "ls"), ["ls", "--color", "/usr/local"])
        self.assertEqual(self.ob.build_cmdline(args=["infile", "outfile"]), ["myprogram", "infile", "outfile"])

    def test_run(self):
        self.ob.prog = "ls"
        self.assertEqual(self.ob.run("/usr/local", color=True), None)

if __name__ == "__main__":
    unittest.main()
