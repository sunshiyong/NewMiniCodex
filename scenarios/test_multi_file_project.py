"""Scenario: Create a multi-file project"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import json
from src.tools import write_file, read_file, run_command

print("=" * 50)
print("Scenario 3: Create a multi-file project")
print("=" * 50)

utils = '''def greet(name):
    return f"Hello, {name}!"
def add(a, b):
    return a + b
'''
r1 = json.loads(write_file("project/utils.py", utils))
print(f"[1/4] Created project/utils.py ({r1['size']} bytes)")

main_script = '''import sys; sys.path.insert(0, ".")
from project.utils import greet, add
print(greet("MiniCodex"))
print(f"2 + 3 = {add(2, 3)}")
'''
r2 = json.loads(write_file("project/main.py", main_script))
print(f"[2/4] Created project/main.py ({r2['size']} bytes)")
r3 = json.loads(write_file("project/__init__.py", ""))
print(f"[3/4] Created project/__init__.py")
r4 = json.loads(run_command("python project/main.py"))
print(f"[4/4] Output:\n{r4['stdout'].strip()}")
assert "Hello, MiniCodex!" in r4["stdout"], "Missing greeting"
assert "2 + 3 = 5" in r4["stdout"], "Wrong calculation"
print("\nPASS: Multi-file project runs correctly")
