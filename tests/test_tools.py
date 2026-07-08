"""Unit tests for tools.py"""

import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import json
import unittest
import shutil
from pathlib import Path
from src.tools import read_file, write_file, run_command
from src.config import SANDBOX_DIR


def clean_sandbox():
    """Remove all files in sandbox except .gitkeep"""
    for item in SANDBOX_DIR.iterdir():
        if item.name == ".gitkeep":
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


class TestPathSafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        clean_sandbox()

    def test_write_then_read(self):
        r = json.loads(write_file("test_hello.txt", "hello world"))
        self.assertEqual(r["action"], "created")
        self.assertEqual(r["size"], 11)

        r2 = json.loads(read_file("test_hello.txt"))
        self.assertEqual(r2["content"], "hello world")

    def test_overwrite_file(self):
        write_file("overwrite_test.txt", "v1")
        r = json.loads(write_file("overwrite_test.txt", "v2"))
        self.assertEqual(r["action"], "modified")
        self.assertEqual(r["old_size"], 2)

    def test_read_nonexistent(self):
        r = json.loads(read_file("nonexistent_file_xyz.txt"))
        self.assertIn("error", r)

    def test_sandbox_escape_write(self):
        r = json.loads(write_file("../escape_test.txt", "bad"))
        self.assertIn("error", r)

    def test_sandbox_escape_deep(self):
        r = json.loads(write_file("../../etc/passwd", "bad"))
        self.assertIn("error", r)

    def test_read_absolute_path(self):
        test_file = os.path.abspath(__file__)
        r = json.loads(read_file(test_file))
        self.assertIn("content", r)
        self.assertIn("def test_read_absolute_path", r["content"])


class TestCommandExecution(unittest.TestCase):
    def test_run_python(self):
        r = json.loads(run_command('python -c "print(42)"'))
        self.assertEqual(r["return_code"], 0)
        self.assertEqual(r["stdout"].strip(), "42")

    def test_run_fail(self):
        r = json.loads(run_command('python -c "raise Exception()"'))
        self.assertEqual(r["return_code"], 1)

    def test_blocked_command(self):
        r = json.loads(run_command("rm -rf /"))
        self.assertIn("error", r)
        self.assertIn("Blocked", r["error"])


class TestNestedDir(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        clean_sandbox()

    def test_write_and_read_nested(self):
        r = json.loads(write_file("nested/a/b/c/deep.txt", "deep"))
        self.assertEqual(r["action"], "created")
        self.assertTrue((SANDBOX_DIR / "nested" / "a" / "b" / "c" / "deep.txt").exists())
        r2 = json.loads(read_file("nested/a/b/c/deep.txt"))
        self.assertEqual(r2["content"], "deep")


if __name__ == "__main__":
    unittest.main()
