# Demonstration recording

Duration: 5 minutes 36 seconds. Automated browser capture with synthesized narration.

**Scope:** The model adapter is scripted. SDK Runner calls, MCP subprocess requests, tool results, errors, and SQLite effects execute during the recording. This is not a live OpenAI model recording.

The browser console is a local recording harness, not an extra MCP tool. Four scenario JSON files in evidence/ preserve actual outputs from the recording.

## 00:00 - Campus Reading Toolkit

This is Campus Reading, a small MCP toolkit for the Agent Tools assignment. It contains exactly one data tool, one action tool, and one orchestration tool. The data tool searches a demonstration library catalogue. The action tool saves a known book to a persistent reading list. The orchestration tool finds a match and saves it. This recording uses an explicitly scripted model adapter because no funded OpenAI API key is configured. The Agents SDK, MCP connection, server execution, and database effects are real. This is an offline integration demonstration, not a live language model evaluation.

## 00:42 - One host, one client, one server

The Python application acts as the host. It owns the user request, the agent configuration, and the model choice. Inside that host, the SDK's MCP Server Stdio object manages the protocol client. It starts a separate FastMCP server process and communicates over standard input and output. Tool discovery returns descriptions and JSON schemas. The Runner executes the selected capability and passes its actual result back to the model adapter. The offline adapter only decides the predefined call. It does not bypass the client, server, or storage. In live mode, an OpenAI model makes that selection.

## 01:24 - 01 / Data tool

Now the browser triggers a real SDK run with the request, find books about artificial intelligence. The scripted adapter emits search catalog, and the SDK routes that invocation through MCP to the server. The result contains two catalogue records, B zero zero one and B zero zero four. Search matches all query words across the title, author, and subjects, ignoring case. The tool has a structured result containing the query, count, and books. The database state below shows that no database exists yet. This verifies the read only boundary. A blank query produces a clear invalid query error.

## 02:06 - 02 / Action tool

The next request explicitly asks to save book B zero zero three to the course list. The action tool validates that the ID exists and that the list label is valid. It then performs a real SQLite insert and returns a receipt with the title, status, list name, and timestamp. The database panel now contains one row. A composite primary key prevents duplicate entries. Repeating the same save returns already saved and preserves the original timestamp. This matters because an agent or client may retry a request. An unknown book ID is rejected instead of creating an invalid reading list entry.

## 02:48 - 03 / Orchestration tool

Here the request asks to find a book about agents and save it. The SDK calls the orchestration tool once through MCP. Inside that tool, the search function runs first, followed by the save function. These are the same domain implementations used by the two primitive tools, so validation and persistence rules stay consistent. There are two matching books. The documented rule chooses the lowest book ID, B zero zero one. The combined result reports the match count, both step names, and the actual save receipt. The database now has two entries. These internal steps are not separate network calls.

## 03:30 - 04 / Predictable failure

For the failure case, the request asks for a book about quantum gardening. Nothing matches the fixture catalogue. The orchestration stops before the save function and returns a no match error. That error travels back through MCP to the SDK, and the offline adapter reports the actual returned content. The database remains at two rows, so failure does not create a phantom entry. The distinction is useful: an empty result is valid for a simple search, but it prevents an orchestration whose goal requires a save. Tests also cover invalid inputs, unknown books, unavailable catalogue data, and storage failures.

## 04:12 - Verification and design tradeoffs

The verification suite contains eighteen passing tests. It checks the single purpose domain behavior, predictable failures, durable storage, and duplicate handling. A subprocess integration test discovers exactly three tools, checks their schemas, calls them through MCP, and restarts the server to confirm persistence. Another test runs the real Agents SDK Runner with the offline adapter. Function spies verify that orchestration calls search before save. These checks establish that the implementation works across the protocol boundary. They do not establish that a live language model selects the correct tool. That separate evaluation requires the configured API key.

## 04:54 - Reflection and submission

The main design decision was to draw boundaries around observable effects. Search only retrieves data, save persists one known item, and the planner owns the combined workflow. Three tools are enough for this focused example, though a real application would also need list inspection and removal. Future work would connect a real library catalogue, add user isolation, and improve selection beyond the lowest ID rule. The package includes source code, setup instructions, tests, the reading summary, reflection, and evidence. This local recording uses synthesized narration and an offline adapter. A live model recording and hosted repository and video links remain separate final submission steps.

## Live-model replacement

Configure OPENAI_API_KEY and run `python agent.py --chat`. Use the four prompts in README.md. Show source code and the database, introduce all three categories, discuss failures and reflection, and record 5-7 minutes. Publish code and video to your chosen accounts and insert actual URLs into SUBMISSION.md.
