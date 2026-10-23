# Code Snippets

Standalone, throwaway scripts used to explore the **streaming** side of the
OpenAI-compatible chat API (the same local [Ollama](https://ollama.com) /
`qwen3:4b` setup the main [Simple AI Assistant](../README.md) uses). They are
learning/reference snippets, not part of the assistant's runtime — nothing in the
main app imports them.

| Script | What it demonstrates |
|--------|----------------------|
| [`stream_test.py`](stream_test.py) | Streaming a plain text completion token-by-token and reassembling the full reply. |
| [`stream_tools_test.py`](stream_tools_test.py) | Streaming a **tool-calling** response and reassembling fragmented `tool_calls` from the deltas. |

## Prerequisites

These scripts reuse the main project's configuration and dependencies:

- Python 3.11+ (developed on 3.14)
- Packages: `openai`, `python-dotenv` (installed in the project's `.venv`)
- A running OpenAI-compatible endpoint (local Ollama by default)
- A `.env` file **in the project root** (`../.env`) with:

  ```ini
  BASE_URL=http://127.0.0.1:11434/v1
  API_KEY=dummy_key
  MODEL=qwen3:4b
  ```

> **Important — run from the project root.** Both scripts call `load_dotenv()`,
> which looks for `.env` in the current working directory, and
> `stream_tools_test.py` additionally does `from tools import TOOLS`, which
> resolves against [`../tools.py`](../tools.py). Run them from the project root so
> both the `.env` and `tools.py` are found:
>
> ```bash
> cd "Simple AI Assistant"
> source .venv/bin/activate
> python "Code Snippets/stream_test.py"
> python "Code Snippets/stream_tools_test.py"
> ```

## `stream_test.py`

Sends a single user message ("Explain what an API is in 100 words…") with
`stream=True` and prints the response as it arrives.

How it works:

1. Loads config from `.env` and creates the `OpenAI` client.
2. Calls `client.chat.completions.create(..., stream=True)`, which yields a
   sequence of chunks instead of one response.
3. Iterates the chunks, skipping any with no `choices` (some servers emit empty
   chunks), and pulls `chunk.choices[0].delta.content`.
4. Prints each non-empty piece immediately (`flush=True`) for a live typing
   effect, while accumulating `full_response`.
5. Prints the reassembled `full_response` at the end — the form you'd append to
   a conversation history.

**Key idea:** in streaming mode the text arrives in fragments; you concatenate
the `delta.content` pieces to rebuild the complete message.

## `stream_tools_test.py`

Sends a tool-triggering message ("What is the weather in Pune?") with the
project's `TOOLS` schema and `stream=True`, then reconstructs the tool call(s)
from the streamed deltas.

How it works:

1. Loads config and `TOOLS` from the main project's [`tools.py`](../tools.py).
2. Streams the completion with `tools=TOOLS`.
3. For each chunk, walks `delta.tool_calls`. Because a single tool call is split
   across many chunks, it keeps a `calls` dict keyed by `tc.index` and, using a
   `SimpleNamespace` placeholder, **appends** the streamed fragments:
   - `id` (set once when it appears)
   - `function.name` (concatenated)
   - `function.arguments` (concatenated JSON string)
4. After the stream ends, it orders the calls by index into `calls_list`.

**Key idea:** tool calls stream in pieces too. You accumulate each call by its
`index` until the stream completes, producing whole tool-call objects. This
snippet stops at *assembling* the calls — it does not execute them (the main
assistant's `run_tool` in [`../tools.py`](../tools.py) handles execution in the
non-streaming path).

## Notes

- These are experiments, not tested utilities — expect to tweak the hard-coded
  prompts while exploring.
- For the full, interactive assistant (non-streaming, with tool execution and
  chained tool calls), see the [project README](../README.md).
