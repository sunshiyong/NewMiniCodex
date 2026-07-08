# -*- coding: utf-8 -*-
"""MiniCodex TUI - AI programming assistant (Day 11: Plan mode + multi-turn)"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from src.agent_loop import AgentLoop

console = Console()

STYLES = {
    "user": "green", "ai": "blue", "tool_call": "yellow",
    "tool_result": "green", "system": "magenta", "error": "red", "plan": "cyan",
}

PREFIXES = {
    "user": "\U0001f7e2 [you]",
    "ai": "\U0001f535 [AI]",
    "tool_call": "\U0001f7e1 [tool]",
    "tool_result": "\U0001f7e2 [result]",
    "system": "\u26aa [sys]",
    "error": "\U0001f534 [err]",
    "plan": "\U0001f4cb [plan]",
}

HELP = """Available:
  /plan  - Plan mode (AI proposes plan first, confirm before execute)
  /exec  - Execute mode (AI executes directly)
  /clear - Clear screen and conversation
  /help  - Show this help
  exit   - Quit"""


class MiniCodexTUI:
    def __init__(self):
        self.display_msgs = []
        self.agent_msgs = None
        self.plan_mode = False
        self.agent = AgentLoop()

    def add_msg(self, t, c):
        self.display_msgs.append((t, c))

    def render_header(self):
        mode = "[bold yellow]Plan[/]" if self.plan_mode else "[bold green]Execute[/]"
        title = "MiniCodex - AI coding assistant"
        hint = "mode: " + mode + " | /plan /exec /clear /help | exit/quit"
        panel = Panel("[bold cyan]" + title + "[/]\n[dim]" + hint + "[/]", style="cyan")
        console.print(panel)
        console.print()

    def render_msgs(self):
        if not self.display_msgs:
            console.print("[dim]Enter your request, AI will help...[/]")
            console.print()
            return
        for t, c in self.display_msgs[-30:]:
            color = STYLES.get(t, "white")
            pref = PREFIXES.get(t, "")
            console.print(Panel(pref + " " + c, style=color, border_style=color))

    def do_cmd(self, inp):
        c = inp.strip().lower()
        if c in ("exit", "quit", "q"):
            return "quit"
        if c in ("/plan", "/p"):
            self.plan_mode = True
            self.add_msg("system", "Switched to Plan mode")
            return "ok"
        if c in ("/exec", "/e"):
            self.plan_mode = False
            self.add_msg("system", "Switched to Execute mode")
            return "ok"
        if c in ("/clear", "/c"):
            self.display_msgs = []
            self.agent_msgs = None
            return "ok"
        if c in ("/help", "/h"):
            self.add_msg("system", HELP)
            return "ok"
        return None

    def on_step(self, step_type, data):
        if step_type == "tool_call":
            args = data.get("args", {})
            s = ", ".join(str(k) + "=" + str(v) for k, v in args.items())
            console.print(Panel(
                PREFIXES["tool_call"] + " " + data["name"] + "(" + s + ")",
                style="yellow", border_style="yellow"))
        elif step_type == "tool_result":
            r = (data.get("result") or "")[:150]
            console.print(Panel(PREFIXES["tool_result"] + " " + r,
                style="green", border_style="green"))
        elif step_type == "text":
            console.print(Panel(PREFIXES["ai"] + " " + data["content"],
                style="blue", border_style="blue"))
        elif step_type in ("stuck", "limit"):
            console.print(Panel(PREFIXES["error"] + " " + data["content"],
                style="red", border_style="red"))
        elif step_type == "plan":
            console.print(Panel(PREFIXES["plan"] + " " + data["content"],
                style="cyan", border_style="cyan"))

    def run_agent(self, user_input):
        self.add_msg("user", user_input)
        console.print()
        steps, msgs = self.agent.run(
            user_input, on_step=self.on_step,
            existing_messages=self.agent_msgs)
        self.agent_msgs = msgs
        for s in steps:
            if s["type"] == "text":
                self.add_msg("ai", s["content"])
            elif s["type"] == "tool":
                self.add_msg("tool_call", s["name"])

    def run(self):
        while True:
            console.clear()
            self.render_header()
            self.render_msgs()

            inp = Prompt.ask("\n[bold cyan]>>[/]")
            rc = self.do_cmd(inp)
            if rc == "quit":
                console.print("[bold cyan]Bye![/]")
                break
            if rc == "ok":
                continue
            if not inp.strip():
                continue

            if self.plan_mode:
                # Phase 1: Generate plan
                console.print(Panel(
                    "[plan] " + inp + "\n[dim]AI is formulating plan...[/]",
                    style="cyan", border_style="cyan"))
                steps, plan_msgs = self.agent.run(
                    inp, on_step=self.on_step,
                    existing_messages=None, plan_only=True)
                plan_text = ""
                for s in steps:
                    if s["type"] == "text":
                        plan_text = s["content"]
                        break
                if plan_text:
                    self.add_msg("plan", plan_text)
                console.print()
                ok = Prompt.ask("[bold yellow]Execute? (Y/n)[/]", default="y")
                if ok.lower() not in ("", "y", "yes"):
                    self.add_msg("system", "Cancelled")
                    continue
                # Phase 2: Execute
                self.add_msg("system", "Executing...")
                self.agent_msgs = plan_msgs
                steps2, msgs2 = self.agent.run(
                    "Execute the plan above, summarize when done",
                    on_step=self.on_step, existing_messages=self.agent_msgs)
                self.agent_msgs = msgs2
                for s in steps2:
                    if s["type"] == "text":
                        self.add_msg("ai", s["content"])
            else:
                self.run_agent(inp)

            # Satisfaction
            console.print()
            ok = Prompt.ask("[bold green]Satisfied? (Y/n)[/]", default="y")
            if ok.lower() in ("n", "no"):
                self.add_msg("system", "Please continue...")
            else:
                self.add_msg("system", "Done")

if __name__ == "__main__":
    MiniCodexTUI().run()
