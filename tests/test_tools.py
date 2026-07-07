"""Tool system tests"""
import sys; sys.path.insert(0, "..")
import json
from src.tools import write_file, read_file, run_command

def test_write_read():
    r = json.loads(write_file("test.txt", "hello"))
    assert r["action"] == "created"
    r2 = json.loads(read_file("test.txt"))
    assert r2["content"] == "hello"
    print("PASS: write+read")

def test_escape():
    r = json.loads(write_file("../bad.txt", "nope"))
    assert "error" in r
    print("PASS: sandbox escape blocked")

def test_run():
    r = json.loads(run_command("python -c \"print(42)\""))
    assert r["stdout"].strip() == "42"
    print("PASS: run_command")

if __name__ == "__main__":
    test_write_read()
    test_escape()
    test_run()
    print("\nALL PASSED")
