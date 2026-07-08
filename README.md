# MiniCodex
> TUI AI 编程助手 / Terminal AI Coding Assistant

<p align="center">
  <a href="#快速开始">中文</a> •
  <a href="#quick-start">English</a>
</p>

---

## 快速开始 / Quick Start

```bash
# 安装依赖 / Install dependencies
pip install httpx rich python-dotenv

# 配置 / Configure
# 编辑 .env，填入 DEEPSEEK_API_KEY
# Edit .env with your DeepSeek API key

# 运行 / Run
python app.py
```

---

## 功能 / Features

| 中文 | English |
|------|---------|
| **TUI 界面** — Rich 分色显示，消息类型一目了然 | **TUI Interface** — Color-coded Rich terminal UI |
| **Execute 模式** — 直接执行 | **Execute Mode** — Direct execution |
| **Plan 模式** — AI 先出方案，确认后执行 | **Plan Mode** — AI proposes plan, confirm before execute |
| **多轮对话** — 同一会话保持上下文 | **Multi-turn** — Persistent conversation context |
| **安全沙盒** — 所有写操作限制在 sandbox/ | **Sandbox** — All writes confined to sandbox/ |
| **外部参考** — AI 可读取任意文件（只读） | **External Ref** — AI reads any file (read-only) |

消息颜色 / Message colors：
🟢 用户/结果 (user/result)  🔵 AI 回答 (AI response)  🟡 工具调用 (tool call)  🔴 错误 (error)

---

## 命令 / Commands

| 命令 | 功能 | Function |
|------|------|----------|
| `/plan` / `/p` | 切换到 Plan 模式 | Switch to Plan mode |
| `/exec` / `/e` | 切换到 Execute 模式 | Switch to Execute mode |
| `/clear` / `/c` | 清除屏幕和对话 | Clear screen & conversation |
| `/help` / `/h` | 显示帮助 | Show help |
| `exit` / `quit` | 退出 | Exit |

---

## Plan 模式原理 / How Plan Mode Works

**Execute 模式（默认）：** AI 直接调工具执行。
**Plan 模式：** 两阶段执行。

```
用户输入 → Phase 1: AI 只输出方案（tools=None，无法调工具）
                    → 用户确认 Y/N
                    → Phase 2: AI 基于方案执行（带上 tools 参数）
```

关键代码 / Key code:
```python
# plan_only=True → 不传 tools，AI 只能说话
tools_arg = None if plan_only else TOOLS
response = self.client.chat(messages, tools=tools_arg)
```

---

## 架构 / Architecture

```
app.py (TUI) → agent_loop.py → llm_client.py → DeepSeek API
                              → tools.py → sandbox/
```

调用链 / Call chain：
1. TUI 输入 → `agent_loop.run()` 带 `on_step` 回调
2. while 循环：LLM → 解析 → 执行工具 → 结果送回 LLM → 继续
3. 每一步通过回调实时显示 / Each step displayed via callback
4. AI 完成后问「满意吗？」 / Prompt "Satisfied?" after completion

### 模块职责 / Modules

| 模块 | 职责 | Responsibility |
|------|------|----------------|
| `app.py` | TUI 入口，Rich 界面 | TUI entry point |
| `agent_loop.py` | Agent while 循环 + 卡住检测 | Agent loop + stuck detection |
| `llm_client.py` | httpx 调 DeepSeek + 自动重试 | LLM client + auto-retry |
| `tools.py` | 文件读写 + 命令执行 + 安全校验 | File I/O + commands + security |
| `config.py` | 配置管理 | Configuration |

---

## 安全机制 / Security

| 机制 | 说明 | Details |
|------|------|---------|
| 路径安全 | `resolve()` 后检查是否在沙盒内 | Path verified after resolve |
| 命令黑名单 | 拦截 rm -rf / format / shutdown 等 | Blocked dangerous commands |
| 超时 | 命令最长 30 秒 | 30s timeout |
| 卡住检测 | 连续 3 次同名工具 → 自动停止 | 3x same tool → auto-stop |

---

## 项目结构 / Project Structure

```
NewMiniCodex/
  app.py              TUI 入口
  src/
    config.py         配置（.env）
    llm_client.py     LLM 客户端
    tools.py          工具系统
    agent_loop.py     Agent 循环
  sandbox/            沙盒目录
  tests/              单元测试（19 个用例）
    test_tools.py
    test_llm_client.py
  scenarios/          场景测试（3 个）
    test_create_and_run.py
    test_external_reference.py
    test_multi_file_project.py
```

---

## 测试 / Testing

```bash
# 单元测试 / Unit tests（19/19 ✅）
python -m unittest discover tests -v

# 场景测试 / Scenario tests（3/3 ✅）
python scenarios/test_create_and_run.py
python scenarios/test_external_reference.py
python scenarios/test_multi_file_project.py
```

---

## 技术选型 / Tech Stack

| 组件 | 选择 | Why |
|------|------|-----|
| LLM API | DeepSeek (OpenAI 兼容) | 已有 API Key |
| HTTP 客户端 | httpx | 零额外依赖 |
| TUI 框架 | rich | 系统已有 |
| 数据模型 | dataclass | 标准库，代替 pydantic |
| 测试框架 | unittest | 标准库，代替 pytest |

---

## 依赖 / Dependencies

- `httpx` — HTTP client for DeepSeek API
- `rich` — Terminal UI framework
- `python-dotenv` — Environment variable loading

## License

MIT
