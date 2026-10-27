<!-- ╔══════════════════════════════════════════════════════════════════╗ -->
<!-- ║                         LOCAL AI AGENT                             ║ -->
<!-- ╚══════════════════════════════════════════════════════════════════╝ -->

<div align="center">

<!-- Hand-crafted animated gradient banner (assets/hero.svg) -->
<a href="https://github.com/Meher-1999/Python-AI-Agent-Ollama">
  <img src="assets/hero.svg" alt="Local AI Agent — Python · Ollama · Tool Calling · built from scratch" width="100%"/>
</a>

<br/><br/>

<!-- Self-made animated, cycling tagline (assets/typing.svg) -->
<img src="assets/typing.svg" alt="No paid API key · It remembers, uses tools and chains them · Runs 100% on your laptop" width="720"/>

<br/><br/>

<!-- Tech badges -->
<img src="https://img.shields.io/badge/Python-3.11+-4B8BBE?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11+"/>
<img src="https://img.shields.io/badge/Ollama-Local_LLM-000000?style=for-the-badge&logo=ollama&logoColor=white" alt="Ollama"/>
<img src="https://img.shields.io/badge/OpenAI–Compatible-API-5A4FCF?style=for-the-badge&logo=openai&logoColor=white" alt="OpenAI-compatible API"/>
<img src="https://img.shields.io/badge/Model-qwen3:4b-7C5CFF?style=for-the-badge" alt="Model qwen3:4b"/>

<br/>

<img src="https://img.shields.io/badge/Tool_Calling-enabled-2ea043?style=flat-square" alt="Tool calling"/>
<img src="https://img.shields.io/badge/Chained_Calls-up_to_5_steps-2ea043?style=flat-square" alt="Chained tool calls"/>
<img src="https://img.shields.io/badge/Runs-100%25_offline-2ea043?style=flat-square" alt="Runs offline"/>
<img src="https://img.shields.io/badge/Cost-%240.00-2ea043?style=flat-square" alt="Zero cost"/>

</div>

---

A minimal, **built-from-scratch** command-line AI agent that chats from your
terminal and can call **real tools** — the current time, live weather, your
location — to answer questions. It talks to any OpenAI-compatible chat API, and
by default a local [Ollama](https://ollama.com) server running the `qwen3:4b`
model, so it runs **fully offline with no API costs and no agent framework**.

> 🧠 **It remembers** the conversation · 🔧 **It uses tools** when they help ·
> 🔗 **It chains them** across multiple steps to resolve one question.

## ✨ Features

- **🗣️ Interactive chat loop** — type questions, get answers, until you say `exit`.
- **⌨️ Streaming replies** — answers are printed **token-by-token as they arrive**
  (via `stream_chat`), for a live typing effect instead of waiting for the full
  response. Press **Ctrl+C** to stop a reply mid-stream and get your prompt back.
- **🧠 Conversation memory** — the full `messages` history is kept (your messages,
  the agent's replies, tool calls, and tool results), so the agent remembers
  earlier turns for context.
- **🔧 Tool calling** — the model decides when to call a tool and the agent runs it:
  | Tool | What it does |
  |------|--------------|
  | `get_current_time` | Current date/time for any IANA timezone. |
  | `get_city_weather` | Current weather for a city (via [wttr.in](https://wttr.in)). |
  | `get_user_city` | The user's home city, for "weather at my place"-style questions. |
- **🔗 Chained tool calls** — the model can call several tools across up to
  `MAX_STEPS` (5) rounds to resolve one question (e.g. look up your city, *then*
  fetch its weather).
- **🐛 Debug logging** — set `DEBUG=True` to see tool calls and results in gray.
- **🔌 Provider-agnostic** — point it at any OpenAI-compatible endpoint by editing `.env`.

## 🗂️ Project structure

```
Python-AI-Agent-Ollama/
├── simple_ai_assistant.py   # Entry point: chat loop + tool-calling orchestration
├── tools.py                 # Tool definitions, implementations, and dispatch
├── Utilities/
│   └── utilities.py         # Debug logging helper (gray DEBUG trace)
├── Code Snippets/           # Standalone streaming experiments (see its README)
│   ├── stream_test.py       # Streaming a plain text completion
│   └── stream_tools_test.py # Streaming + reassembling tool calls
├── requirements.txt         # Python dependencies
├── .env.example             # Template for your local .env
└── .env                     # Your configuration (not committed)
```

## 📦 Requirements

- **Python 3.11+** (developed on 3.14)
- An **OpenAI-compatible chat endpoint**. The default config expects
  [Ollama](https://ollama.com) running locally.

Python dependencies (see [`requirements.txt`](requirements.txt)):

- `openai`
- `python-dotenv`
- `requests`

## 🚀 Setup

**1. Clone and enter the project**

```bash
git clone https://github.com/Meher-1999/Python-AI-Agent-Ollama.git
cd Python-AI-Agent-Ollama
```

**2. Create a virtual environment and install dependencies**

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**3. Start Ollama and pull the model** (for the default local setup)

```bash
ollama pull qwen3:4b
ollama serve
```

**4. Create your `.env` file**

```bash
cp .env.example .env
```

Then adjust the values if needed:

```ini
BASE_URL=http://127.0.0.1:11434/v1
API_KEY=dummy
MODEL=qwen3:4b
DEBUG=False
```

| Variable   | Description                                                        |
|------------|--------------------------------------------------------------------|
| `BASE_URL` | Base URL of the OpenAI-compatible API (note the `/v1`).            |
| `API_KEY`  | API key. Any non-empty value works for local Ollama.              |
| `MODEL`    | Model name to use for completions (run `ollama list` for names).   |
| `DEBUG`    | Set to `True` to print tool calls and results; anything else off. |

## ▶️ Usage

```bash
python simple_ai_assistant.py
```

Then chat at the prompt:

```text
👦🏻 User: what time is it in London?
🤖 Assistant: It's 2026-10-20 20:15:03 BST in London.

👦🏻 User: how's the weather where I live?
🤖 Assistant: Los Angeles: ☀️ +24°C

👦🏻 User: exit
Exiting the assistant. Goodbye!
```

Replies stream in live as the model generates them. Type `exit`, `quit`, `bye`,
or `goodbye` to leave, or press **Ctrl+C** to interrupt a reply that's streaming.

## 🔄 Control flow

```mermaid
flowchart TD
    START([Start]) --> INIT[Initialize<br/>OpenAI client, system prompts,<br/>TOOLS &amp; function mapping]
    INIT --> LOOP[Start chat loop]
    LOOP --> INPUT["Get user input<br/>(User: prompt)"]
    INPUT --> EXIT{"Exit command?<br/>(exit, quit, bye, goodbye)"}
    EXIT -->|Yes| DONE([Exit])
    EXIT -->|No| APPEND[Append user message to history]
    APPEND --> CALL[Call model with TOOLS<br/>client.chat.completions.create]
    CALL --> TOOLS{"Any tool calls?<br/>(msg.tool_calls)"}
    TOOLS -->|Yes| ATOOL[Append assistant message<br/>with tool calls]
    ATOOL --> RUN[For each tool call:<br/>run_tool &rarr; execute mapped function<br/>get_current_time / get_city_weather / get_user_city]
    RUN --> ARES[Append tool result to history]
    ARES --> CALL
    TOOLS -->|No| AMSG[Append assistant message to history]
    AMSG --> PRINT["Print assistant response<br/>(Assistant: + content)"]
    PRINT --> INPUT
    CALL -. step limit reached<br/>MAX_STEPS = 5 .-> FALLBACK[Print fallback message]
    FALLBACK --> INPUT
```

The model/tool loop (`Call model` → `Any tool calls?` → run tools → call again) repeats
up to `MAX_STEPS` (5) times per user question. If the model never returns a plain
answer within that budget, the agent prints a fallback message and waits for the
next input.

## ⚙️ How it works

1. User input is appended to the running `messages` history.
2. The agent sends the conversation plus the `TOOLS` schema to the model with
   `stream=True`. `stream_chat` prints text **token-by-token as it arrives** and
   reassembles any streamed tool-call fragments into whole calls.
3. If the model requests tool calls, `build_tool_calls_payload` converts the
   reassembled calls into the assistant message, each is dispatched through
   `run_tool` ([`tools.py`](tools.py)), and the results are appended to history.
4. Steps 2–3 repeat until the model returns a plain answer, or until
   `MAX_STEPS` (5) rounds are used — after which it returns a fallback message.
5. The streamed answer is kept in history (as `full_response`) for context.
   Press **Ctrl+C** to stop a reply mid-stream.

The system prompts keep replies in English and under 100 words — tweak them at
the top of [`simple_ai_assistant.py`](simple_ai_assistant.py) to change the
agent's behavior.

## ➕ Adding a new tool

1. Write the function in [`tools.py`](tools.py).
2. Add its JSON schema to the `TOOLS` list.
3. Register it in `FUNCTION_NAME_TO_FUNCTION_MAP`.

The agent will then be able to call it automatically when relevant.

## 🧪 Experiments

The [`Code Snippets/`](Code%20Snippets/) folder holds standalone scripts that
explore the OpenAI-compatible API beyond the main app — **streaming** chat and
tool calls, plus early **embeddings / semantic search** work using the
`nomic-embed-text` model (the groundwork for RAG). They are learning/reference
snippets — nothing in the main app imports them. See the
[Code Snippets README](Code%20Snippets/README.md) for details.

## 📝 Notes

- `get_user_city` is hard-coded to `"Los Angeles"` — edit it in
  [`tools.py`](tools.py) to set your own city.
- `.env` holds configuration and should **not** be committed to version control
  (it is already in `.gitignore`); copy [`.env.example`](.env.example) instead.
- 🔁 **Docs stay in sync:** a project hook
  ([`.claude/hooks/remind-readme.sh`](.claude/hooks/remind-readme.sh)) reminds
  the assistant to update this README whenever a Python source file changes.

<div align="center">

<img src="assets/footer.svg" alt="" width="100%"/>

<sub>Built with 🐍 Python · 🦙 Ollama · ⚡ OpenAI-compatible tool calling — no framework, no cloud, no cost.</sub>

</div>
