# open-agent-framework

A self-hosted agentic LLM platform powered by [Ollama](https://ollama.com). Run autonomous coding agents locally — no API keys, no usage costs, no data leaving your machine.

> Born out of frustration with existing local AI tooling. The goal: a Claude Code-style coding agent that runs entirely on local models.

---

## What it does

- **Wraps Ollama** in a clean FastAPI layer with auto-start and model management
- **Autonomous agent loop** — the LLM reasons, calls tools, observes results, and iterates until the task is done
- **Built-in tools**: read files, write files, run shell commands, search codebases
- **Streaming support** — stream agent steps in real time via Server-Sent Events
- **Fully containerised** — one `docker-compose up` and you're running

```
User prompt
    │
    ▼
┌─────────────────────────────────┐
│           Agent Loop            │
│  THOUGHT → ACTION → OBSERVE     │◄──┐
│        (repeat)                 │   │
└────────────┬────────────────────┘   │
             │ tool call              │ tool result
             ▼                        │
┌─────────────────────────────────┐   │
│         Tool Registry           │───┘
│  read_file │ write_file         │
│  run_command │ search_files     │
└─────────────────────────────────┘
             │
             ▼
         ANSWER
```

---

## Quickstart

### With Docker (recommended)

```bash
# 1. Clone
git clone https://github.com/pvgmenegasso/open-agent-framework.git
cd open-agent-framework

# 2. Configure
cp .env.example .env
# edit .env if needed (default model: llama3)

# 3. Start everything (Ollama + API + model pull)
docker-compose up --build

# 4. Try it
curl -X POST http://localhost:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{"task": "List all Python files in /workspace and summarise what each one does.", "model": "llama3"}'
```

### Locally (without Docker)

```bash
# Requires: Python 3.11+, Ollama installed and running

pip install -r requirements-dev.txt
uvicorn api.main:app --reload
```

---

## API

### `POST /agent/run`
Run the agent to completion. Returns all reasoning steps and the final answer.

```json
{
  "task": "Read /workspace/main.py and find any potential bugs.",
  "model": "llama3"
}
```

Response:
```json
{
  "steps": [
    {
      "thought": "I should read the file first.",
      "action": "read_file",
      "params": {"path": "/workspace/main.py"},
      "tool_result": {"success": true, "output": "..."}
    }
  ],
  "answer": "I found the following potential issues: ..."
}
```

### `POST /agent/stream`
Same as `/agent/run` but streams steps as [Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events).

```bash
curl -N -X POST http://localhost:8000/agent/stream \
  -H "Content-Type: application/json" \
  -d '{"task": "Write a fizzbuzz in /workspace/fizzbuzz.py", "model": "llama3"}'
```

### `GET /models/`
List locally available models.

### `POST /models/pull`
Pull a model from the Ollama registry.

```json
{"models": ["codellama", "mistral"]}
```

### `GET /health`
Health check.

---

## Available Tools

| Tool | Description |
|------|-------------|
| `read_file` | Read file contents, optionally by line range |
| `write_file` | Write or append to a file, creates dirs as needed |
| `run_command` | Execute a shell command with timeout and safety blocklist |
| `search_files` | grep-style pattern search across a directory |

### Adding your own tool

```python
# agent/tools/my_tool.py
from agent.tool import Tool, ToolResult

class MyTool(Tool):
    name = "my_tool"
    description = "Does something useful."
    parameters = {
        "input": {"type": "string", "description": "The input.", "required": True}
    }

    async def run(self, input: str) -> ToolResult:
        result = do_something(input)
        return ToolResult(tool_name=self.name, success=True, output=result)
```

Then register it in `api/main.py`:
```python
registry.register(MyTool())
```

---

## GPU Support

Uncomment the `deploy` block in `docker-compose.yml` and ensure you have [nvidia-container-toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) installed.

---

## Project structure

```
open-agent-framework/
├── agent/
│   ├── loop.py          # Agentic reasoning loop
│   ├── tool.py          # Tool base class + registry
│   └── tools/
│       ├── read_file.py
│       ├── write_file.py
│       ├── run_command.py
│       └── search_files.py
├── api/
│   ├── main.py          # FastAPI app + lifespan wiring
│   └── routes/
│       ├── agent.py     # /agent endpoints (run + stream)
│       └── models.py    # /models endpoints
├── client/
│   └── ollama_client.py # Ollama wrapper (async, streaming, model mgmt)
├── tests/
│   └── test_tools.py
├── Dockerfile
├── docker-compose.yml
└── .github/workflows/ci.yml
```

---

## Roadmap

- [ ] Persistent conversation memory across sessions
- [ ] Helm chart for Kubernetes deployment
- [ ] Web UI (chat interface for the agent)
- [ ] MCP (Model Context Protocol) tool integration
- [ ] Support for multi-agent workflows (planner + executor)
- [ ] Configurable model backends (beyond Ollama — LM Studio, vLLM)

---

## Development

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Lint
ruff check .
```

---

## Why this exists

Available local agent solutions were either too opinionated, too tightly coupled to cloud providers, or too complex to self-host cleanly. This project is an attempt at a minimal, hackable, platform-engineer-friendly foundation — something you can actually understand, modify, and deploy.

---

## License

MIT
