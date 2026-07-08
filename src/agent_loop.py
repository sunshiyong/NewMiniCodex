"""Agent 核心循环 — 支持多轮对话 + Plan/Execute"""

import json

from .config import MAX_STEPS, STUCK_LIMIT, CONTEXT_LIMIT
from .llm_client import LLMClient
from .tools import TOOLS, execute_tool

SYSTEM_PROMPT = (
    "你是一个 AI 编程助手。你的工作方式是："
    "1. 分析用户需求。"
    "2. 调用工具（读文件、写文件、执行命令）来实现。"
    "3. 完成后向用户总结做了什么。\n"
    "规则："
    "- 所有写操作和命令执行都必须在沙盒目录内。"
    "- 读文件可以用绝对路径读取项目外的文件做参考。"
    "- 如果文件已存在，先读再看要不要改。"
    "- 每次修改前先读文件确认内容。"
    "- 改完代码后运行命令验证。"
    "- 不要一次性写大段代码，尽量分步骤来。"
    "- 每次调用工具前先说明要做什么。"
)


class AgentLoop:
    def __init__(self):
        self.client = LLMClient()

    def _truncate(self, messages):
        """上下文截断，保持 assistant/tool 消息对完整性"""
        while self.client.count_tokens(messages) > CONTEXT_LIMIT and len(messages) > 3:
            # 若 messages[1] 是含 tool_calls 的 assistant，必须连同后面的 tool result 一起删
            if (messages[1].get("role") == "assistant" and
                    messages[1].get("tool_calls") and
                    len(messages) > 3 and
                    messages[2].get("role") == "tool"):
                messages = [messages[0]] + messages[3:]
            else:
                messages = [messages[0]] + messages[2:]
        return messages

    def run(self, user_input, on_step=None, existing_messages=None, plan_only=False):
        """
        执行一轮用户请求。

        Args:
            user_input: 用户输入
            on_step: 回调 on_step(step_type, data)
            existing_messages: 上一轮的 messages 列表（多轮对话）
            plan_only: True = 只输出文字计划，不调工具（Plan 模式第一阶段）

        Returns:
            (steps, messages)
            steps: 步骤列表
            messages: 更新后的 messages 列表（传回给下一轮使用）
        """
        steps = []

        if existing_messages:
            messages = list(existing_messages)
            messages.append({"role": "user", "content": user_input})
        else:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input},
            ]

        last_tool = None
        stuck = 0
        count = 0

        while count < MAX_STEPS:
            messages = self._truncate(messages)

            # Plan only mode: 不给 tools，AI 只能文字回答
            tools_arg = None if plan_only else TOOLS
            response = self.client.chat(messages, tools=tools_arg)

            if response.type == "text":
                steps.append({"type": "text", "content": response.content})
                if on_step:
                    on_step("text", {"content": response.content})
                messages.append({"role": "assistant", "content": response.content})
                break

            # tool call
            count += 1
            name = response.name

            if name == last_tool:
                stuck += 1
            else:
                stuck = 0
            last_tool = name

            if stuck >= STUCK_LIMIT:
                msg = f"Stuck: {STUCK_LIMIT}x {name}, stopped"
                steps.append({"type": "text", "content": msg})
                if on_step:
                    on_step("stuck", {"content": msg, "tool": name})
                break

            messages.append({
                "role": "assistant", "content": None,
                "tool_calls": [{
                    "id": response.id, "type": "function",
                    "function": {"name": name, "arguments": json.dumps(response.args, ensure_ascii=False)}
                }]
            })

            if on_step:
                on_step("tool_call", {"name": name, "args": response.args})

            result = execute_tool(name, response.args)
            steps.append({"type": "tool", "name": name, "args": response.args, "result": result[:300]})

            if on_step:
                on_step("tool_result", {"name": name, "result": result[:200]})

            messages.append({"role": "tool", "tool_call_id": response.id, "content": result})

            # 如果 AI 的最后一条是 assistant 消息但没有 tool_calls（即刚追加的），
            # 说明 AI 刚做了文字回复，可以退出
            if messages[-1]["role"] == "assistant" and messages[-1].get("content"):
                break

        if count >= MAX_STEPS:
            msg = f"Reached max steps ({MAX_STEPS})"
            steps.append({"type": "text", "content": msg})
            if on_step:
                on_step("limit", {"content": msg})

        return steps, messages
