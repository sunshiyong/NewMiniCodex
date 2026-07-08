# MiniCodex — TUI AI Coding Assistant

A terminal-based AI coding assistant with a rich TUI interface. Tell it what to build, and AI reads/writes files and runs commands inside a safe sandbox.

## Quick Start

```bash
# Setup
python -m venv .venv
.venv\Scripts\activate
pip install httpx rich python-dotenv

# Configure
cp .env.example .env
# Edit .env with your DeepSeek API key

# Run
python app.py
```

## Features

- **TUI Interface**: Rich terminal UI with color-coded messages
  - \U0001f7e2 User input (green)  |  \U0001f535 AI response (blue)
  - \U0001f7e1 Tool calls (yellow)  |  \U0001f534 Errors (red)
- **Two Modes**:
  - `Execute` mode: AI executes directly on your request
  - `Plan` mode: AI proposes a plan first, you confirm before execution
- **Multi-turn Conversation**: Keep asking follow-up requests in the same session
- **Safety**: All write operations and command execution are confined to `sandbox/`
- **External Reference**: AI can read any file on your system for context

## Commands

| Command | Description |
|---------|-------------|
| `/plan` or `/p` | Switch to Plan mode |
| `/exec` or `/e` | Switch to Execute mode |
| `/clear` or `/c` | Clear screen and conversation |
| `/help` or `/h` | Show help |
| `exit` or `quit` | Exit |

## Project Structure

```
NewMiniCodex/
  app.py              TUI entry point
  src/
    config.py         Configuration (.env + constants)
    llm_client.py     LLM client (httpx, auto-retry, model fallback)
    tools.py          Tool system (read_file / write_file / run_command)
    agent_loop.py     Agent loop (multi-turn, Plan/Execute, stuck detection)
  sandbox/            Safe sandbox directory
  tests/              Unit tests (unittest)
    test_tools.py     Tool system tests (10 tests)
    test_llm_client.py LLM client tests (9 tests)
  scenarios/          Scenario tests
    test_create_and_run.py
    test_external_reference.py
    test_multi_file_project.py
```

## Architecture

```
app.py (TUI) -> agent_loop.py -> llm_client.py -> DeepSeek API
                              -> tools.py -> sandbox/
```

- `app.py` renders the TUI and calls `agent_loop.run()` with an `on_step` callback
- `agent_loop.py` runs the while loop: LLM -> tool_call -> execute -> repeat
- `llm_client.py` wraps httpx calls with auto-retry (2x exponential backoff)
- `tools.py` implements read_file (absolute/relative), write_file (sandbox only), run_command

## Dependencies

- `httpx` — HTTP client for DeepSeek API calls
- `rich` — Terminal UI framework
- `python-dotenv` — Environment variable loading

## Testing

```bash
# Run all unit tests
python -m unittest discover tests -v

# Run scenario tests
python scenarios/test_create_and_run.py
python scenarios/test_external_reference.py
python scenarios/test_multi_file_project.py
```

## License

MIT
