"""Unit tests for llm_client.py — parsing logic only, no API calls"""

import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import json
import unittest
from src.llm_client import ToolCallResponse, TextResponse, LLMClient


class TestResponseModels(unittest.TestCase):
    """响应模型测试"""

    def test_text_response(self):
        r = TextResponse(content="hello")
        self.assertEqual(r.type, "text")
        self.assertEqual(r.content, "hello")

    def test_tool_call_response(self):
        r = ToolCallResponse(id="call_123", name="read_file", args={"path": "test.txt"})
        self.assertEqual(r.type, "tool_call")
        self.assertEqual(r.id, "call_123")
        self.assertEqual(r.name, "read_file")
        self.assertEqual(r.args, {"path": "test.txt"})

    def test_tool_call_defaults(self):
        r = ToolCallResponse()
        self.assertEqual(r.id, "")
        self.assertEqual(r.name, "")
        self.assertEqual(r.args, {})


class TestTokenCounter(unittest.TestCase):
    """Token 估算测试"""

    def setUp(self):
        self.client = LLMClient()

    def test_empty_messages(self):
        self.assertEqual(self.client.count_tokens([]), 0)

    def test_simple_messages(self):
        msgs = [
            {"role": "user", "content": "hello world"},
        ]
        # "hello world" = 11 chars / 4 = 2 tokens
        self.assertEqual(self.client.count_tokens(msgs), 2)

    def test_long_content(self):
        msgs = [
            {"role": "user", "content": "a" * 100},
        ]
        self.assertEqual(self.client.count_tokens(msgs), 25)

    def test_multiple_messages(self):
        msgs = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Write a Python script"},
        ]
        # 30 chars + 21 chars = 51 / 4 = 12
        self.assertEqual(self.client.count_tokens(msgs), 12)


class TestModelConfig(unittest.TestCase):
    """模型配置测试"""

    def test_default_model_set(self):
        client = LLMClient()
        self.assertTrue(len(client.model) > 0)
        self.assertTrue(len(client.fallback_model) > 0)

    def test_model_fallback_available(self):
        client = LLMClient()
        self.assertNotEqual(client.model, client.fallback_model,
                            "Primary and fallback models should differ")


if __name__ == "__main__":
    unittest.main()
