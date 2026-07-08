"""工具系统"""
import json, os, subprocess
from pathlib import Path
from .config import SANDBOX_DIR, RESULT_TRUNCATE

BLOCKED = [
    "del /f /s", "rd /s /q", "rmdir /s", "format", "shutdown", "taskkill /f",
    "rm -rf /", "rm -rf ~", "rm -rf /*", ":(){ :|:& };:", "init 0", "reboot",
]
MAX_READ = 10 * 1024 * 1024

def _safe_path(rel):
    full = (SANDBOX_DIR / rel).resolve()
    if not str(full).startswith(str(SANDBOX_DIR.resolve())):
        raise PermissionError(f"Path escape: {rel}")
    return full

def _safe_cmd(cmd):
    low = cmd.lower().strip()
    for b in BLOCKED:
        if b in low:
            return False, f"Blocked: {b}"
    return True, ""

def read_file(path):
    try:
        full = Path(path).resolve() if os.path.isabs(path) else (SANDBOX_DIR / path).resolve()
        if not full.exists():
            return json.dumps({"error": f"Not found: {path}"})
        if not full.is_file():
            return json.dumps({"error": f"Not a file: {path}"})
        if full.stat().st_size > MAX_READ:
            return json.dumps({"error": "File too large (>10MB)"})
        content = full.read_text("utf-8")
        return json.dumps({"path": str(full), "size": len(content), "content": content})
    except Exception as e:
        return json.dumps({"error": str(e)})

def write_file(path, content):
    try:
        full = _safe_path(path)
        full.parent.mkdir(parents=True, exist_ok=True)
        old = full.read_text("utf-8") if full.exists() else ""
        full.write_text(content, "utf-8")
        return json.dumps({"path": path, "action": "modified" if old else "created", "size": len(content), "old_size": len(old)})
    except Exception as e:
        return json.dumps({"error": str(e)})

def run_command(command, workdir="."):
    safe, reason = _safe_cmd(command)
    if not safe:
        return json.dumps({"error": reason})
    try:
        if workdir == ".":
            cwd = str(SANDBOX_DIR.resolve())
        else:
            resolved = (SANDBOX_DIR / workdir).resolve()
            if not str(resolved).startswith(str(SANDBOX_DIR.resolve())):
                return json.dumps({"error": f"Path escape: {workdir}"})
            cwd = str(resolved)
        r = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True, timeout=30)
        return json.dumps({"command": command, "return_code": r.returncode, "stdout": r.stdout[:RESULT_TRUNCATE], "stderr": r.stderr[:RESULT_TRUNCATE//2]})
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Timeout (30s)"})
    except Exception as e:
        return json.dumps({"error": str(e)})

TOOLS = [
    {"type": "function", "function": {"name": "read_file", "description": "Read file. Relative path = sandbox, absolute path = anywhere (read-only).", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "File path (relative to sandbox or absolute)"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "write_file", "description": "Write file to sandbox. Creates parent dirs. Overwrites if exists.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Relative path in sandbox"}, "content": {"type": "string", "description": "UTF-8 content"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "run_command", "description": "Run command inside sandbox directory.", "parameters": {"type": "object", "properties": {"command": {"type": "string", "description": "Command to run"}, "workdir": {"type": "string", "description": "Working dir (relative to sandbox)"}}, "required": ["command"]}}},
]
TOOLS_MAP = {"read_file": read_file, "write_file": write_file, "run_command": run_command}

def execute_tool(name, args):
    func = TOOLS_MAP.get(name)
    if func:
        return func(**args)
    return json.dumps({"error": f"Unknown tool: {name}"})
