"""MiniCodex TUI — 终端对话式 AI 编程助手"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich.table import Table

from src.agent_loop import AgentLoop
from src.tools import TOOLS

console = Console()


def color_for(msg_type):
    return {
        "user": "green",
        "ai": "blue",
        "tool_call": "yellow",
        "tool_result": "green",
        "system": "magenta",
        "error": "red",
    }.get(msg_type, "white")


def prefix_for(msg_type):
    return {
        "user": "\U0001f7e2 [你]",
        "ai": "\U0001f535 [AI]",
        "tool_call": "\U0001f7e1 [工具]",
        "tool_result": "\U0001f7e2 [结果]",
        "system": "\u26aa [系统]",
        "error": "\U0001f534 [错误]",
    }.get(msg_type, "")


class MiniCodexTUI:
    def __init__(self):
        self.messages = []  # [(type, content), ...]
        self.plan_mode = False
        self.agent = AgentLoop()

    def add_msg(self, msg_type, content):
        self.messages.append((msg_type, content))

    def render_header(self):
        mode_tag = "[bold yellow]Plan[/bold yellow]" if self.plan_mode else "[bold green]Execute[/bold green]"
        header = Panel(
            "[bold cyan]MiniCodex[/bold cyan] \u2014 AI \u7f16\u7a0b\u52a9\u624b"
            f"\n\n[dim]\u6a21\u5f0f: {mode_tag}  |  /plan /exec /clear /help  |  exit/quit \u9000\u51fa[/dim]",
            style="cyan",
        )
        console.print(header)
        console.print()

    def render_messages(self):
        if not self.messages:
            console.print("[dim]\u8f93\u5165\u4f60\u7684\u9700\u6c42\uff0cAI \u5c06\u5e2e\u4f60\u5b9e\u73b0...[/dim]")
            console.print()
            return
        for msg_type, content in self.messages[-30:]:
            c = color_for(msg_type)
            p = prefix_for(msg_type)
            console.print(Panel(f"{p} {content}", style=c, border_style=c))

    def show_mode_prompt(self):
        """In Plan mode, ask user to confirm before execution."""
        if self.plan_mode:
            confirm = Prompt.ask(
                "\n[bold yellow]\u786e\u8ba4\u6267\u884c\uff1f(Y/n)[/bold yellow]",
                default="y",
            )
            return confirm.lower() in ("", "y", "yes")
        return True

    def handle_special_command(self, cmd):
        cmd = cmd.strip().lower()
        if cmd in ("exit", "quit", "q"):
            return "quit"
        if cmd in ("/plan", "/p"):
            self.plan_mode = True
            self.add_msg("system", "\u5207\u6362\u5230 Plan \u6a21\u5f0f\uff1aAI \u5148\u51fa\u65b9\u6848\uff0c\u4f60\u786e\u8ba4\u540e\u6267\u884c")
            return "handled"
        if cmd in ("/exec", "/e"):
            self.plan_mode = False
            self.add_msg("system", "\u5207\u6362\u5230 Execute \u6a21\u5f0f\uff1aAI \u76f4\u63a5\u6267\u884c")
            return "handled"
        if cmd in ("/clear", "/c"):
            self.messages = []
            return "handled"
        if cmd in ("/help", "/h"):
            self.add_msg("system",
                "\u53ef\u7528\u547d\u4ee4\uff1a\n"
                "  /plan  - Plan \u6a21\u5f0f\uff08\u5148\u51fa\u65b9\u6848\u518d\u6267\u884c\uff09\n"
                "  /exec  - Execute \u6a21\u5f0f\uff08\u76f4\u63a5\u6267\u884c\uff09\n"
                "  /clear - \u6e05\u5c4f\n"
                "  /help  - \u5e2e\u52a9\n"
                "  exit   - \u9000\u51fa"
            )
            return "handled"
        return None

    def run_agent(self, user_input):
        """Run agent and display each step live."""
        self.add_msg("user", user_input)
        console.print()

        def on_step(step_type, data):
            if step_type == "tool_call":
                args_str = ", ".join(f"{k}={v}" for k, v in data.get("args", {}).items())
                console.print(Panel(
                    f"{prefix_for('tool_call')} {data['name']}({args_str})",
                    style="yellow", border_style="yellow"
                ))
            elif step_type == "tool_result":
                console.print(Panel(
                    f"{prefix_for('tool_result')} {data['result'][:150]}",
                    style="green", border_style="green"
                ))
            elif step_type == "text":
                console.print(Panel(
                    f"{prefix_for('ai')} {data['content']}",
                    style="blue", border_style="blue"
                ))
            elif step_type == "stuck":
                console.print(Panel(
                    f"{prefix_for('error')} {data['content']}",
                    style="red", border_style="red"
                ))
            elif step_type == "limit":
                console.print(Panel(
                    f"{prefix_for('error')} {data['content']}",
                    style="red", border_style="red"
                ))

        steps = self.agent.run(user_input, on_step=on_step)

        # Collect final text step into messages
        for s in steps:
            if s["type"] == "text":
                self.add_msg("ai", s["content"])
            elif s["type"] == "tool":
                self.add_msg("tool_call", s["name"])

    def run(self):
        while True:
            console.clear()
            self.render_header()
            self.render_messages()

            user_input = Prompt.ask("\n[bold cyan]>>[/bold cyan]")

            # Handle special commands
            result = self.handle_special_command(user_input)
            if result == "quit":
                console.print("[bold cyan]\u518d\u89c1\uff01[/bold cyan]")
                break
            if result == "handled":
                continue
            if not user_input.strip():
                continue

            # Plan mode: show the request and ask for confirmation
            if self.plan_mode:
                console.print(Panel(
                    f"{prefix_for('user')} {user_input}\n\n"
                    "[dim]\u8bf7\u786e\u8ba4\u662f\u5426\u6267\u884c\uff1f[/dim]",
                    style="yellow", border_style="yellow"
                ))
                ok = Prompt.ask("\n[bold yellow]\u786e\u8ba4\u6267\u884c\uff1f(Y/n)[/bold yellow]", default="y")
                if ok.lower() not in ("", "y", "yes"):
                    self.add_msg("system", "\u5df2\u53d6\u6d88")
                    continue

            # Execute
            self.run_agent(user_input)

            # Satisfaction check
            console.print()
            satisfied = Prompt.ask("[bold green]\u6ee1\u610f\u5417\uff1f(Y/n)[/bold green]", default="y")
            if satisfied.lower() in ("n", "no"):
                self.add_msg("system", "\u8bf7\u7ee7\u7eed\u63d0\u4ea4\u9700\u6c42...")
            else:
                self.add_msg("system", "\u2714 \u5df2\u5b8c\u6210")
