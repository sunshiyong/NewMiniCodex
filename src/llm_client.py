"""LLM 客户端 — 直接使用 httpx 调用 DeepSeek API（兼容 OpenAI 格式）"""

import json
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx

from .config import DEEPSEEK_API_KEY, BASE_URL, MODEL, MODEL_FALLBACK


@dataclass
class ToolCallResponse:
    type: str = "tool_call"
    id: str = ""
    name: str = ""
    args: dict = field(default_factory=dict)


@dataclass
class TextResponse:
    type: str = "text"
    content: str = ""


class LLMClient:
    def __init__(self):
        self.model = MODEL
        self.fallback_model = MODEL_FALLBACK

    def _call_api(self, messages, tools, temperature):
        """调用 DeepSeek Chat API"""
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            body["tools"] = tools

        try:
            with httpx.Client(timeout=60) as client:
                resp = client.post(
                    f"{BASE_URL}/chat/completions",
                    headers=headers,
                    json=body,
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.TimeoutException:
            print("  [API Timeout]")
            return None
        except httpx.HTTPStatusError as e:
            print(f"  [API HTTP {e.response.status_code}] {e.response.text[:200]}")
            return None
        except Exception as e:
            print(f"  [API Error] {e}")
            return None

        try:
            choice = data["choices"][0]
            reason = choice.get("finish_reason", "stop")
            msg = choice["message"]
        except (KeyError, IndexError) as e:
            print(f"  [API Parse Error] {e}, raw: {str(data)[:200]}")
            return None

        if reason == "stop":
            return TextResponse(content=msg.get("content", "") or "")

        if reason == "tool_calls":
            tcs = msg.get("tool_calls")
            if not tcs:
                return TextResponse(content="[Tool call error: empty]")
            if len(tcs) > 1:
                names = [tc["function"]["name"] for tc in tcs]
                print(f"  [Warning] {len(tcs)} tool calls ({names}), using first")
            tc = tcs[0]
            try:
                args = json.loads(tc["function"]["arguments"])
            except json.JSONDecodeError:
                args = {}
            return ToolCallResponse(
                id=tc["id"],
                name=tc["function"]["name"],
                args=args,
            )

        content = msg.get("content", "")
        if content:
            return TextResponse(content=content)
        return TextResponse(content=f"[LLM: finish_reason={reason}]")

    def chat(self, messages, tools=None, temperature=0.3):
        """自动重试 2 次 (1s, 3s) + model fallback"""
        for delay, label in [(1, "retry 1 (1s)..."), (3, "retry 2 (3s)...")]:
            result = self._call_api(messages, tools, temperature)
            if result is not None:
                return result
            print(f"  {label}")
            time.sleep(delay)

        # Fallback model
        old = self.model
        self.model = self.fallback_model
        print(f"  Fallback to {self.fallback_model}")
        result = self._call_api(messages, tools, temperature)
        self.model = old
        if result is not None:
            return result
        return TextResponse(content="[API failed after all retries + fallback]")

    def count_tokens(self, messages):
        return sum(len(str(m.get("content", ""))) for m in messages) // 4
