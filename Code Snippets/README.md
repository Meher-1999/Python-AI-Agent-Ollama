# Code Snippets

Standalone, throwaway scripts used to explore the OpenAI-compatible API — both
the **streaming** side of chat and the **embeddings** side used for semantic
search (the same local [Ollama](https://ollama.com) setup the main
[Local AI Agent](../README.md) uses: `qwen3:4b` for chat and `nomic-embed-text`
for embeddings). They are learning/reference snippets, not part of the agent's
runtime — nothing in the main app imports them.

| Script | What it demonstrates |
|--------|----------------------|
| [`stream_test.py`](stream_test.py) | Streaming a plain text completion token-by-token and reassembling the full reply. |
| [`stream_tools_test.py`](stream_tools_test.py) | Streaming a **tool-calling** response and reassembling fragmented `tool_calls` from the deltas. |
| [`test_embedding.py`](test_embedding.py) | Calling the embeddings API (`nomic-embed-text`) on a few sentences and printing a preview of each vector. |
| [`semantic_search_test.py`](semantic_search_test.py) | Embedding texts and comparing them with cosine similarity — the core idea behind semantic search / RAG retrieval *(work in progress)*. |
| [`doc_search.py`](doc_search.py) | A full **semantic document search** pipeline over the [`knowledge_base/`](../knowledge_base/) corpus: load docs → embed → cosine-rank a query → return top-k matches (the retrieval half of RAG). |

## Prerequisites

These scripts reuse the main project's configuration and dependencies:

- Python 3.11+ (developed on 3.14)
- Packages: `openai`, `python-dotenv` (installed in the project's `.venv`). The
  embedding snippets (`test_embedding.py`, `semantic_search_test.py`,
  `doc_search.py`) also need **`numpy`** — `pip install numpy`.
- A running OpenAI-compatible endpoint (local Ollama by default). The embedding
  snippets need the embedding model pulled: `ollama pull nomic-embed-text`.
- For `doc_search.py`: the document corpus in [`../knowledge_base/`](../knowledge_base/)
  (a folder of `.txt` files) and the `KB_FOLDER` env var pointing at it.
- A `.env` file **in the project root** (`../.env`) with:

  ```ini
  BASE_URL=http://127.0.0.1:11434/v1
  API_KEY=dummy_key
  MODEL=qwen3:4b
  EMBED_MODEL=nomic-embed-text   # used by the embedding snippets
  KB_FOLDER=knowledge_base       # corpus folder, used by doc_search.py
  ```

> **Important — run from the project root.** Both scripts call `load_dotenv()`,
> which looks for `.env` in the current working directory, and
> `stream_tools_test.py` additionally does `from tools import TOOLS`, which
> resolves against [`../tools.py`](../tools.py). Run them from the project root so
> both the `.env` and `tools.py` are found:
>
> ```bash
> cd Python-AI-Agent-Ollama
> source .venv/bin/activate
> python "Code Snippets/stream_test.py"
> python "Code Snippets/stream_tools_test.py"
> python "Code Snippets/test_embedding.py"
> python "Code Snippets/semantic_search_test.py"
> python "Code Snippets/doc_search.py"
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

## `test_embedding.py`

The first step toward RAG: turning text into vectors. Sends three sentences to
`client.embeddings.create(model="nomic-embed-text", ...)` and prints the first
five numbers of each returned embedding.

How it works:

1. Loads config from `.env` and creates the `OpenAI` client.
2. Calls the **embeddings** endpoint (not chat) with a list of input strings.
3. Iterates `response.data` and prints a short preview (`emb.embedding[:5]`) of
   each vector.

**Key idea:** an embedding is a fixed-length list of floats that captures the
*meaning* of a piece of text — the foundation for semantic comparison.

## `semantic_search_test.py`

Builds on embeddings to show how **semantic similarity** is measured. Defines two
helpers and a few sample sentences:

- `get_embedding(text)` — returns one embedding using the `EMBED_MODEL` env var
  (`nomic-embed-text`).
- `cosine_similarity(A, B)` — scores how close two vectors are, via
  `numpy.dot(A, B) / (‖A‖·‖B‖)`; ~1.0 means very similar, ~0 means unrelated.

**Key idea:** semantic search embeds a query and each candidate, then ranks
candidates by cosine similarity — the retrieval step at the heart of RAG.

> **Work in progress.** This snippet currently sets up the helpers and sample
> texts but doesn't yet embed and compare them end-to-end, so it produces no
> output on its own. It also needs `numpy` installed and `EMBED_MODEL` set (see
> Prerequisites).

## `doc_search.py`

The full semantic-search pipeline `semantic_search_test.py` was building toward —
a runnable **document retrieval** system over the real [`knowledge_base/`](../knowledge_base/)
corpus (HR, leave, medical, travel, tech docs, etc.). This is the **retrieval
half of RAG**: given a question, it finds the most relevant documents by meaning.

How it works:

1. **`load_documents(folder=KB_FOLDER)`** — reads every `.txt` file in the corpus
   folder into `{source, text}` records.
2. **`add_embeddings(documents)`** — calls `get_embedding()` on each document and
   stores the resulting vector on the record.
3. **`get_embedding(text)`** — one embedding via the `EMBED_MODEL` (`nomic-embed-text`).
4. **`cosine_similarity(A, B)`** — `numpy.dot(A, B) / (‖A‖·‖B‖)`.
5. **`search(query, documents, top_k=3)`** — embeds the query, scores it against
   every pre-embedded document, sorts by similarity, and returns the top-k
   `{score, source, text, size}` matches.
6. A `test()` helper prints the ranked results, and the script runs a sample
   query (*"How many days will I get for maternity leave?"*) end-to-end.

**Key idea:** embed the corpus once, then answer a query by embedding it and
ranking documents by cosine similarity — exactly the retrieval step a RAG agent
runs before feeding the top matches to the chat model. This snippet does the
**retrieve**; it does not yet generate an answer or wire into the agent.

> **Standalone for now.** `doc_search.py` is not imported by the main app — it
> embeds the whole corpus on every run (no caching) and uses a hard-coded query.
> It needs `numpy`, `EMBED_MODEL`, `KB_FOLDER`, and the `knowledge_base/` folder
> (see Prerequisites).

## Notes

- These are experiments, not tested utilities — expect to tweak the hard-coded
  prompts while exploring.
- For the full, interactive assistant (non-streaming, with tool execution and
  chained tool calls), see the [project README](../README.md).
