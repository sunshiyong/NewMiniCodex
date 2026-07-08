"""Scenario: Create a Python script, run it, verify output"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import json
from src.tools import write_file, read_file, run_command

print("=" * 50)
print("Scenario 1: Create and run a Python script")
print("=" * 50)

script = '''def fib(n):
    a, b = 0, 1
    for _ in range(n):
        print(a, end=" ")
        a, b = b, a + b
    print()

if __name__ == "__main__":
    fib(10)
'''
r1 = json.loads(write_file("fib.py", script))
print(f"[1/3] Created fib.py ({r1['size']} bytes)")
r2 = json.loads(read_file("fib.py"))
print(f"[2/3] Verified content ({r2['size']} bytes)")
r3 = json.loads(run_command("python fib.py"))
print(f"[3/3] Output: {r3['stdout'].strip()}")
assert "0 1 1 2 3 5 8 13 21 34" in r3["stdout"], "Unexpected output!"
print("\nPASS: Fibonacci sequence correct")
