import sys; sys.path.insert(0, ".")
import json
from src.tools import write_file, read_file, run_command

r1 = write_file("test.txt", "hello minicodex")
print("write:", json.loads(r1))

r2 = read_file("test.txt")
print("read:", json.loads(r2)["content"])

r3 = run_command("python -c \"print(123)\"")
print("run:", json.loads(r3)["stdout"][:50])

# Test absolute path read (external file)
r4 = read_file(__file__)
print("abs read:", json.loads(r4)["size"], "bytes")

# Test sandbox escape
r5 = write_file("../evil.txt", "bad")
print("escape:", json.loads(r5).get("error", "none")[:20])

print("\nALL OK")
