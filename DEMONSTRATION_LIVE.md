# Demonstration recording

Duration: 5 minutes 36 seconds. Automated browser capture with synthesized narration.

**Scope:** Live gpt-4.1-mini model calls through the OpenAI Agents SDK and a real stdio MCP server. Tool selection is performed by the model. Four fresh requests execute during browser capture. Narration is synthesized. Actual outputs are preserved in evidence/live_video_scenario_1.json through live_video_scenario_4.json.

## 00:00 - Campus Reading Toolkit

This is Campus Reading, an MCP toolkit for the Agent Tools assignment. It contains exactly one data tool, one action tool, and one orchestration tool. Search retrieves books from a small demonstration catalogue. Save adds a known book to a persistent reading list. Plan reading combines those operations. This recording uses a live OpenAI model through the OpenAI Agents SDK. The model chooses its tool calls from the descriptions discovered over MCP. The browser will trigger fresh requests during this recording. Tool execution, returned results, and database effects are real.

## 00:42 - One host, one client, one server

The Python application is the MCP host. It owns the user request, agent instructions, and model configuration. The SDK MCP Server Stdio object manages the client connection to a separate FastMCP subprocess. The client discovers exactly three tools, with descriptions and input and output schemas. The Runner sends the available tools to the live model. When the model selects a tool, the SDK invokes it through MCP, receives the result, and asks the model for its response. The protocol connects the components; the model makes the language based routing decision.

## 01:24 - 01 / Data tool

The browser now submits a fresh request to find books about artificial intelligence. The live model selects search catalog, and the SDK sends that invocation through the MCP client to the server. Search uses case insensitive matching across the title, author, and subjects. It returns two matching records with IDs B zero zero one and B zero zero four. The assistant response below is generated from that actual result. The independent database panel shows that no database exists yet. This verifies that the data tool retrieves information without changing the reading list.

## 02:06 - 02 / Action tool

The next request explicitly asks the live model to save B zero zero three to the course list. The model selects save reading item. The server validates that the book exists and the list label is valid, then inserts a row into SQLite. Its receipt reports the actual status, book, list, and timestamp. The database panel independently confirms one saved row. A uniqueness constraint makes this operation idempotent: repeating the same book and list pair returns already saved, preserving the original timestamp. Unknown IDs fail before writing. This tool has one observable effect: persisting a known item.

## 02:48 - 03 / Orchestration tool

This request asks to find a book about agents and save it. The live model selects the orchestration tool, plan reading. One MCP invocation reaches the server. Inside that operation, the same search function used by the data tool runs first, followed by the same save function used by the action tool. Two books match, and the documented selection rule chooses the lowest book ID. The result reports both internal steps and a real save receipt. The database now contains two entries. This separates the model choosing a higher level capability from the deterministic workflow inside the server.

## 03:30 - 04 / Predictable failure

Now the live model receives a request for a book about quantum gardening. The catalogue has no match, so the planner stops before saving and returns a clear no match error. The actual error travels back through the MCP client to the Runner. The model then explains the failure to the user instead of inventing a successful save. The independent database check still shows two rows. An empty result is valid for a data lookup, but it prevents a workflow whose goal requires saving a matching book. Tests also cover invalid inputs, unknown IDs, catalogue failures, and storage errors.

## 04:12 - Verification and design tradeoffs

Eighteen automated tests passed. They verify domain behavior, predictable failures, duplicate handling, and persistent storage. The subprocess test discovers exactly three tools, checks their schemas, calls them over MCP, and restarts the server to verify persistence. Function spies check that orchestration runs search before save. An offline SDK adapter remains available for reproducible testing without API charges. Separately, the live model scenario suite selected all three tools successfully. The recording adds fresh live requests and preserves their outputs. These are focused examples, not an exhaustive evaluation of every possible user request.

## 04:54 - Reflection and submission

The boundaries follow observable effects: lookup reads information, action persists one item, and orchestration coordinates the combined request. Three tools are enough for this focused demonstration. A larger application would need list inspection, removal, a real catalogue service, and user specific storage. The written summary critiques the reference Fetch server and explains the MCP host, client, and server roles. The submission includes source code, configuration, tests, reflection, and this live recording. Repository and video hosting links still need publication to the chosen accounts. The local package does not invent external URLs or include an API key.

