"""Scenario: Read external file as reference, create new file"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import json
from src.tools import read_file, write_file

print("=" * 50)
print("Scenario 2: Read external file, create new file based on reference")
print("=" * 50)

test_file = os.path.abspath(__file__)
r1 = json.loads(read_file(test_file))
print(f"[1/3] Read external file ({r1['size']} bytes)")
assert "Scenario 2" in r1["content"], "Should contain scenario name"

new_content = f"""\"\"\"Generated from reference: {os.path.basename(__file__)}\""\"
print("Hello from generated file!")
"""
r2 = json.loads(write_file("generated_from_ref.py", new_content))
print(f"[2/3] Created generated file ({r2['size']} bytes)")
r3 = json.loads(read_file("generated_from_ref.py"))
print(f"[3/3] Verified ({r3['size']} bytes)")
print("\nPASS: External reference workflow works")
