# Campus Reading MCP Toolkit

Hassan Nasrallah - EECE503P - C5 Agent Tools

Submission links: [Source repository](https://github.com/han33-dotcom/eece503p-campus-reading-mcp) | [Live demonstration video, 5:36](https://drive.google.com/file/d/18dwtMw_RwCStCVLHslIfjr2hzP4SiQsM/view).

Exactly **three MCP tools**, built with FastMCP and connected through the OpenAI Agents SDK. The small local catalogue is demonstration data, not an official university catalogue. Saving modifies a real SQLite database, not a reservation or borrowing system.

| Category | MCP tool | Inputs | Structured output | Predictable failure |
|---|---|---|---|---|
| Data | `search_catalog` | `query: str`, `limit: int = 5` | SearchResult: query, count, books | INVALID_QUERY / INVALID_LIMIT |
| Action | `save_reading_item` | `book_id: str`, `list_name: str = "course"` | SaveResult: status, list_name, book, saved_at | UNKNOWN_BOOK / STORAGE_UNAVAILABLE |
| Orchestration | `plan_reading` | `query: str`, `list_name: str = "course"` | PlanResult: query, selection_rule, matches, steps, saved | NO_MATCH; no write |

All returned models and their field types are defined in `library.py`. FastMCP publishes input and output JSON schemas. No extra MCP resources or prompts are exposed: the read-only lookup is deliberately an MCP **tool**, as required by the brief.

## Setup (Windows PowerShell)

Python 3.12 was used for verification. Run from this folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Alternatively, `./run_demo.ps1 -Offline` creates the virtual environment and runs the offline demo; `./run_demo.ps1 -Test` runs tests. `./run_demo.ps1 -Chat` runs live chat and also recognizes an API key saved in the Windows user environment.

Direct dependencies are pinned to the versions tested. `evidence/requirements-lock.txt` records the complete tested environment (some extra packages there were used only for recording). Dependencies were resolved from PyPI on October 29, 2026.

## Live OpenAI agent

Set a funded key in your own shell. `.env.example` is a template; files named `.env` are not loaded automatically.

```powershell
$env:OPENAI_API_KEY = "your-own-key"
$env:OPENAI_MODEL = "gpt-4.1-mini"
.\.venv\Scripts\python.exe agent.py --chat
```

The model can be changed to another tool-capable model available to your API account. Example prompts:

1. `Find books about artificial intelligence.`
2. `Save book B003 to my course list.`
3. `Find a book about agents and save it to my course list.`
4. `Find a book about quantum gardening and save it to my course list.`

Run `python agent.py` for this same four-scenario suite with a live model. `--json-output evidence/live_demo.json` saves its results. The suite was verified with live gpt-4.1-mini calls: the model selected search_catalog, save_reading_item, and plan_reading, then explained the no-match error. Actual results are saved in evidence/live_demo.json and evidence/live_demo.txt. If the key is missing, live mode exits with a clear message. It never silently falls back to the scripted model.

## Reproducible offline SDK demonstration

```powershell
.\.venv\Scripts\python.exe agent.py --offline --json-output evidence/offline_demo.json
```

`ScriptedDemoModel` implements the SDK Model interface and emits predefined tool calls. **It is a test double, not an OpenAI model and not proof of LLM reasoning.** The SDK Runner, tool discovery, stdio transport, FastMCP execution, validation, errors, and SQLite effects are real. The final response includes the actual returned tool content. `evidence/` contains recorded runs and tests. The primary submission video is demonstration_live.mp4, which uses a live OpenAI model. The earlier offline demonstration.mp4 is retained as supplemental evidence. Both use automated browser capture and synthesized narration. See DEMONSTRATION_LIVE.md and DEMONSTRATION.md for their respective scopes.

## Architecture and tool design

```text
User -> Python host (Agent + Runner; live model or explicit test double)
     -> SDK MCPServerStdio client
     -> stdio JSON-RPC -> FastMCP server subprocess
                         |-- search_catalog -> local catalogue (read only)
                         |-- save_reading_item -> SQLite (persistent action)
                         `-- plan_reading -> search function -> save function
     <- structured tool result / MCP error <- SDK <- assistant response
```

The host configures one client/server connection; this does not discover arbitrary network servers. `plan_reading` uses the **same domain implementations** as the other tools, in sequence. It is one MCP invocation with two internal steps, not three separate protocol calls. Tests spy on the two functions to verify their order. The selection rule is the lowest book ID among all matches; catalogue size is five, below the orchestration search limit of ten.

Single-purpose descriptions, typed schemas, explicit errors, and deterministic ordering make calls predictable. Search uses all-word, case-insensitive substring matching. An empty search result is valid for the data tool; the orchestration treats it as NO_MATCH because it cannot fulfil a save. A failed search never creates a database. Save validates the book and list label before writing. A unique `(list_name, book_id)` key makes retries idempotent. SQLite transactions keep individual writes atomic; this small project does not claim a distributed transaction across independent services.

The database defaults to `runtime/reading_list.sqlite3`. Set `LIBRARY_DB` to another path to isolate runs. List names are labels, not file paths. The application has no multi-user authentication and is intended for local single-user use. Catalogue text and tool results are untrusted data; the live-agent instructions say to treat them as data. Read-only annotations describe behavior; they are not access-control enforcement. Tracing is disabled to keep this demonstration self-contained.

## Files and submission status

- `server.py`, `library.py`: server and typed domain logic.
- `agent.py`, `offline_model.py`: live host and explicit offline test adapter.
- `test_toolkit.py`: domain failures, persistence/idempotency, exact tool count, schemas, subprocess MCP, and SDK Runner checks.
- `SUMMARY.md`: 300-400 word reading/exploration summary with sources.
- `REFLECTION.md`: two-paragraph reflection.
- `demonstration_live.mp4`: primary narrated live-model demonstration.
- `demonstration.mp4`: supplemental narrated offline demonstration.
- `DEMONSTRATION_LIVE.md`, `DEMONSTRATION.md`: timed narration scripts and evidence scope.
- `SUBMISSION.md`: deliverable map and remaining external submission steps.

No API secret is included. Source code is published in the public repository linked above. The live recording is hosted on Google Drive with anyone-with-the-link Viewer access. A local Git bundle and both recordings are also supplied in the downloadable assignment package. Final Moodle submission is left to the student.

## Documentation consulted

- [FastMCP tools](https://gofastmcp.com/servers/tools)
- [OpenAI Agents SDK MCP](https://openai.github.io/openai-agents-python/mcp/)
- [OpenAI Agents SDK overview](https://developers.openai.com/api/docs/guides/agents/sdk)
- Reading sources and the Fetch server are cited in `SUMMARY.md`.
