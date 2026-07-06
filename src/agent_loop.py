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
        while self.client.count_tokens(messages) > CONTEXT_LIMIT and len(messages) > 3:
            messages = [messages[0]] + messages[2:]
        return messages

    def run(self, user_input, on_step=None):
        """
        执行一轮用户请求。

        Args:
            user_input: 用户输入
            on_step: 回调函数 on_step(step_type, data)
                step_type: "tool_call" | "tool_result" | "text" | "stuck" | "limit"
        """
        steps = []
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ]

        last_tool = None
        stuck = 0
        count = 0

        while count < MAX_STEPS:
            messages = self._truncate(messages)
            response = self.client.chat(messages, tools=TOOLS)

            if response.type == "text":
                steps.append({"type": "text", "content": response.content})
                if on_step:
                    on_step("text", {"content": response.content})
                break

            count += 1
            name = response.name

            # stuck detection
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

            # append assistant message
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

        if count >= MAX_STEPS:
            msg = f"Reached max steps ({MAX_STEPS})"
            steps.append({"type": "text", "content": msg})
            if on_step:
                on_step("limit", {"content": msg})

        return steps
