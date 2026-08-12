# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@.claude/TASKS.local.md

## Project overview

An AI chatbot/copilot that connects **IBM Maximo Asset Management** (OSLC REST API) to **Ollama** (currently `gpt-oss:120b-cloud`, run via a local `ollama serve` proxying to Ollama Cloud) via a hand-rolled tool-calling loop, exposed through a FastAPI backend and a React (`@assistant-ui/react`) frontend. The backend is designed to run as an AWS Lambda function (via Mangum) behind API Gateway, and also runs locally with uvicorn.

## Commands

### Toolbx Environment (`dev` container)

This system uses Fedora Toolbx. All dev commands (python, uvicorn, node, npm, etc.) must be run inside the `dev` toolbox container:
```bash
toolbox run -c dev <command>
```

### Backend (Python, run from repo root)

```bash
toolbox run -c dev source venv/bin/activate
toolbox run -c dev uvicorn main:app --reload --port 8000
```


There is no lint/format tooling configured for the Python code (no ruff/black/flake8 config present).

### Frontend (`frontend/`)

```bash
cd frontend
npm install
npm run dev        # vite dev server at http://localhost:5173
npm run build       # tsc -b && vite build
npm run lint        # eslint .
npm run preview
```

Frontend talks to the backend via `VITE_API_BASE_URL` (see `frontend/src/App.tsx`); it falls back to a hardcoded deployed API Gateway URL if unset.

### Testing

`test_backend.py` is a manual script, not a pytest suite — run it directly (`python test_backend.py`). It calls `run_tests()` which hits a locally-reachable Ollama daemon (`ollama serve`, model set via `OLLAMA_MODEL`) and, through tool calls, the live Maximo API, with `time.sleep()` calls between requests. Running it requires `ollama serve` running (and `ollama signin` if `OLLAMA_MODEL` points at a `-cloud` model) plus a working `.env` with real `MAXIMO_API_KEY` values.

### Deployment (AWS Lambda)

Build a Linux-compatible dependency bundle and zip it with the source, per `README.md`:

```bash
mkdir -p build_pkg
pip install --target ./build_pkg --platform manylinux2014_x86_64 \
  --implementation cp --python-version 3.11 --only-binary=:all: -r requirements.txt
cd build_pkg && zip -q -r ../lambda_deploy.zip . && cd ..
zip -q -g lambda_deploy.zip main.py ollama_client.py tool_schemas.py maximo_client.py maximo_mcp_server.py .env
```

Lambda handler is `main.handler` (Mangum-wrapped FastAPI app), runtime Python 3.11, deployed behind an API Gateway HTTP API with an `ANY /{proxy+}` route. `lambda_deploy.zip` is a build artifact checked into the working tree at times but is gitignored — don't hand-edit it. Note: `OLLAMA_HOST` defaults to `http://localhost:11434`, which isn't reachable from inside Lambda — a real deployment needs `OLLAMA_HOST` pointing at an Ollama instance Lambda can actually reach over the network.

## Architecture

Request flow: **React SPA → API Gateway → Lambda (FastAPI/Mangum) → Ollama (`gpt-oss:120b-cloud`, hand-rolled tool-calling loop) → Maximo OSLC REST API**.

- **`main.py`** — FastAPI app. Single real endpoint `POST /api/chat` (plus `GET /` health check reporting `OLLAMA_MODEL`). `chat_endpoint` calls `chat_with_tools()` from `ollama_client.py`.
- **`ollama_client.py`** — Owns the Ollama HTTP calls and the tool-calling loop. `chat_with_tools()` POSTs to `{OLLAMA_HOST}/api/chat` (Ollama's native API, not the OpenAI-compat shim) with the system prompt and `TOOL_SCHEMAS`; since Ollama has no automatic function calling, the loop is hand-written: read `tool_calls` off the response, validate each call's arguments through the matching Pydantic model in `tool_schemas.py`, call the real function, append a `role: "tool"` result message, and resend — up to `max_rounds`. The assistant message is appended back into history unmodified (not rebuilt) so a reasoning model's `thinking` content, if present, survives across tool-call rounds.
- **`tool_schemas.py`** — Defines `ServiceRequestArgs`/`LocationArgs`/`ClassificationArgs` (Pydantic models mirroring the `fetch_*` function signatures below) and builds `TOOL_SCHEMAS` (Ollama's `{"type": "function", "function": {...}}` shape, via `.model_json_schema()`) plus the `TOOL_FUNCTIONS`/`TOOL_ARG_MODELS` name-keyed lookup tables `ollama_client.py` dispatches through.
- **`maximo_mcp_server.py`** — Wraps the `maximo_client.py` functions as `@mcp.tool()`-decorated MCP tools (`fetch_service_requests`, `fetch_locations`, `fetch_classifications`). Their docstrings double as the tool `description` text in `tool_schemas.py`.
- **`maximo_client.py`** — All direct HTTP calls to the Maximo OSLC REST API (`MXAPISR`, `MXAPILOCATION`, `MXAPICLASSSTRUCTURE`). Handles:
  - Building `oslc.where` clauses, including turning comma/"and"/"or"-separated user input into OSLC `in [...]` clauses (`_format_in_clause`).
  - Stripping OSLC/RDF metadata (`spi:` prefixes, `_`-prefixed and `_collectionref`-suffixed keys) via `_clean_oslc_member`.
  - Deduplicating result members by a domain-specific unique key (`_deduplicate_items`) since OSLC queries with joined hierarchies can return duplicate rows.
  - A `count_only` short-circuit that uses `?count=1` to return `totalCount` without fetching full payloads.
- **`frontend/src/App.tsx`** — Single-file React app built on `@assistant-ui/react` primitives (`ThreadPrimitive`, `MessagePrimitive`, `ComposerPrimitive`). Implements a custom `ChatModelAdapter` (`maximoAdapter`) that POSTs the latest user message to the backend `/api/chat` and returns the reply as a single text part — there's no streaming and no message history sent to the backend (only `message`, despite `ChatRequest` on the backend accepting `history`). Markdown/GFM table rendering uses `@assistant-ui/react-markdown` + `remark-gfm`.

### Key conventions
- All three Maximo resource fetchers (`get_service_requests`, `get_locations`, `get_classifications`) follow the same shape: build `oslc.where`/`oslc.select` params → optional `count_only` short-circuit → fetch → clean → dedupe → truncate to `limit`. Follow this pattern when adding a new Maximo resource.
- Env vars (`OLLAMA_HOST`, `OLLAMA_MODEL`, `MAXIMO_BASE_URL`, `MAXIMO_API_KEY`) are loaded via `python-dotenv` from `.env` (see `.env.example` for the required set). `OLLAMA_HOST` defaults to `http://localhost:11434`; `OLLAMA_MODEL` defaults to `gpt-oss:120b-cloud`, which routes through Ollama Cloud via the local daemon (needs `ollama signin`, no `ollama pull`) — swap it for a fully local model name any time with no code change. `GEMINI_API_KEY`/`GEMINI_MODEL` are still read from `.env.example` but unused by the current code (left over from before the Ollama swap).
- `.claude/skills/*` and `.agents/skills/*` are symlinked assistant-ui skill docs (pulled via `skills-lock.json` from `assistant-ui/skills` on GitHub) — consult them for `@assistant-ui/react` API questions (runtime, primitives, streaming, tools, markdown, thread-list, etc.) rather than guessing at the library's API.
