# MiniCodex — TUI AI 编程助手 / AI Coding Assistant

[English](#english) | [中文](#中文)

---

<a id="中文"></a>

## MiniCodex — TUI AI 编程助手

终端中的 AI 编程助手，Rich TUI 交互界面。用自然语言告诉它你想写什么，AI 在安全的沙盒中自动读写文件、执行命令。

### 快速开始

```bash
# 安装依赖
python -m venv .venv
.venv\Scripts\activate
pip install httpx rich python-dotenv

# 配置 API Key
cp .env.example .env
# 编辑 .env，填入你的 DeepSeek API Key

# 运行
python app.py
```

### 功能特性

| 特性 | 说明 |
|------|------|
| **TUI 界面** | Rich 终端界面，消息分色显示 |
| **双模式** | Execute 模式（直接执行） / Plan 模式（先出方案，确认后执行） |
| **多轮对话** | 同一会话中持续追加需求，AI 保留上下文 |
| **安全沙盒** | 所有写操作和命令执行限制在 `sandbox/` 目录 |
| **外部参考** | AI 可以读取你电脑上的任意文件做参考（只读） |

消息颜色：
- 🟢 **绿色** — 用户输入 / 工具执行结果
- 🔵 **蓝色** — AI 回答
- 🟡 **黄色** — 工具调用（含参数）
- 🔴 **红色** — 错误信息
- 🟣 **紫色** — 系统消息

### 命令

| 命令 | 功能 |
|------|------|
| `/plan` 或 `/p` | 切换到 Plan 模式 |
| `/exec` 或 `/e` | 切换到 Execute 模式 |
| `/clear` 或 `/c` | 清除屏幕和对话历史 |
| `/help` 或 `/h` | 显示帮助 |
| `exit` 或 `quit` | 退出 |

### Plan 模式 vs Execute 模式

**Execute 模式（默认）：**
AI 收到需求后直接调用工具执行，步骤实时显示在界面上。

**Plan 模式：**
1. AI 先输出执行方案（不调任何工具）
2. 用户审阅方案，按 Y 确认或 N 取消
3. 确认后 AI 按方案执行

在 Plan 模式下，AI 调用时 `tools` 参数设为 `None`，AI 只能输出文字，无法调用工具。确认后第二阶段的调用才带上 `tools` 参数。

### 项目结构

```
NewMiniCodex/
  app.py              TUI 入口（Rich）
  src/
    config.py         配置（.env + 常量）
    llm_client.py     LLM 客户端（httpx + 自动重试 + 模型降级）
    tools.py          工具系统（read_file / write_file / run_command）
    agent_loop.py     Agent 循环（多轮对话 + Plan/Execute + 卡住检测）
  sandbox/            安全沙盒目录
  tests/              单元测试
    test_tools.py     工具测试（10 个用例）
    test_llm_client.py LLM 客户端测试（9 个用例）
  scenarios/          场景测试
    test_create_and_run.py        创建并运行脚本
    test_external_reference.py    读取外部文件做参考
    test_multi_file_project.py    创建多文件项目
```

### 架构

```
app.py (TUI) → agent_loop.py → llm_client.py → DeepSeek API
                              → tools.py → sandbox/
```

调用链：
1. 用户在 TUI 输入需求
2. `app.py` 调用 `agent_loop.run()`，传入 `on_step` 回调
3. Agent 循环：调 LLM → 解析响应 → 执行工具 → 结果送回 LLM → 继续
4. 每一步通过回调实时显示在 TUI 上
5. AI 输出最终结果后，TUI 显示「满意吗？」确认

### 安全机制

- **路径安全**：所有文件操作先 `resolve()` 成绝对路径，再检查前缀是否在沙盒内
- **命令黑名单**：拦截 `rm -rf`、`format`、`shutdown` 等危险命令（Windows + Linux）
- **超时保护**：命令执行最长 30 秒
- **卡住检测**：连续 3 次调用同一工具 → 自动停止

### 技术选型

| 组件 | 选择 | 理由 |
|------|------|------|
| LLM API | DeepSeek (OpenAI 兼容) | 已有 API Key，支持 Function Calling |
| HTTP | httpx | 0 依赖，免安装 |
| TUI | rich | 系统已有，零额外依赖 |
| 模型定义 | dataclass | Python 标准库，代替 pydantic |
| 测试 | unittest | Python 标准库，代替 pytest |

### 测试

```bash
# 运行所有单元测试
python -m unittest discover tests -v

# 运行场景测试
python scenarios/test_create_and_run.py
python scenarios/test_external_reference.py
python scenarios/test_multi_file_project.py
```

### 依赖

- `httpx` — HTTP 客户端（调 DeepSeek API）
- `rich` — 终端 UI 框架
- `python-dotenv` — 环境变量加载

---

<a id="english"></a>

## MiniCodex — TUI AI Coding Assistant (English)

A terminal-based AI coding assistant with a rich TUI interface powered by Rich. Describe what you want to build in natural language, and the AI reads/writes files and runs commands inside a safe sandbox.

[Features | Commands | Architecture | Testing — see Chinese section above for details]

### Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install httpx rich python-dotenv
# Edit .env with your DeepSeek API key
python app.py
```

### Test Results

```
Unit tests: 19/19 passed
  test_tools.py       — 10 tests (write/read/overwrite/escape/absolute-path/command/nested)
  test_llm_client.py  — 9 tests (models/response/token-counting)

Scenario tests: 3/3 passed
  Create and run Fibonacci script
  Read external file as reference, create new file
  Create multi-file project and execute
```

### License

MIT
