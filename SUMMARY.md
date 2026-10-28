# Reading and exploration summary

**Hassan Nasrallah | EECE503P | C5 - Agent Tools**

## Summary

Ksenia Se's Hugging Face article presents Model Context Protocol as a response to a practical limitation: language models need current information and useful actions beyond their training data. Custom integrations create repeated work because every application must otherwise connect separately to every service. MCP provides a shared interface for exposing capabilities, making integrations easier to reuse across compatible applications. The article links to a longer Turing Post explanation, which discusses discovering tools, resources, and prompt templates through a configured connection. Discovery does not mean arbitrary servers are automatically trusted or connected. [1][2]

The architecture separates three responsibilities. The host is the user-facing AI application that manages the conversation, model, and access policy. A client inside that host manages the protocol connection to a particular server. The server exposes capabilities and executes requests against its underlying data or services. In my implementation, the Python agent application is the host, the Agents SDK's MCPServerStdio manages the client connection, and the FastMCP subprocess is the server. The model chooses tools in live mode; MCP transports requests and results rather than supplying intelligence itself. [2][3]

I explored the reference Fetch MCP server's Python implementation. Its fetch capability accepts a URL and returns webpage content, optionally simplified into Markdown. Its typed parameters document controls such as output length, starting position, and raw content. This gives the agent a relatively narrow, understandable contract. Fetching and formatting are multiple internal steps, but they serve one coherent outcome: obtaining readable content from a URL. They do not also create unrelated reminders or modify the user's files. [4]

The implementation anticipates network failures, HTTP errors, and autonomous-fetch restrictions, reporting explicit errors. Bounded output improves predictability and protects the model's context budget. Nevertheless, extraction may discard useful page structure, and raw versus simplified output increases behavioral variation. I would make that tradeoff especially clear in the description and test both modes against representative pages. [4]

For my toolkit, this critique motivates typed inputs, structured receipts, deterministic selection, and a strict separation between lookup and persistence. The orchestration tool owns the combined workflow explicitly. This keeps individual capabilities reusable while making side effects visible to the agent and the user.

## References

Sources inspected on October 29, 2026. The summary above excludes these references from its word count.

1. Ksenia Se, [Hugging Face MCP article](https://huggingface.co/blog/Kseniase/mcp).
2. Ksenia Se, [linked full explanation on Turing Post](https://www.turingpost.com/p/mcp).
3. OpenAI, [Agents SDK MCP documentation](https://openai.github.io/openai-agents-python/mcp/).
4. MCP reference servers, [Fetch implementation](https://github.com/modelcontextprotocol/servers/blob/main/src/fetch/src/mcp_server_fetch/server.py).
