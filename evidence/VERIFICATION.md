# Verification record

Date: October 29, 2026 (Asia/Beirut).

- Python: 3.12, isolated virtual environment.
- FastMCP: 4.1.4; OpenAI Agents SDK: 0.24.0; MCP Python SDK: 2.3.0.
- Latest FastMCP and OpenAI Agents SDK package versions checked using PyPI before installation.
- `python -m pytest -q`: **18 passed in 12.31s**. Full output: tests.txt.
- `python -m pip check`: **No broken requirements found**.
- Tool discovery: exactly search_catalog, save_reading_item, and plan_reading. Actual discovered schemas are preserved in tool_schemas.json.
- Offline SDK scenario results: offline_demo.json and offline_demo.txt. Model selection is scripted; the Runner and tool execution are real.
- Four additional SDK/MCP scenarios execute during the browser recording. video_scenario_1.json through video_scenario_4.json contain their actual outputs.
- Independently checked SQLite effects: lookup leaves no database; direct action creates B003; orchestration adds B001; NO_MATCH leaves the same two rows.
- Written summary: 359 whitespace-delimited words excluding headings and references.
- Dependency snapshot: requirements-lock.txt. Recording-only packages are included in that full environment snapshot.

## Limits of the evidence

A funded key was subsequently configured and the live gpt-4.1-mini suite completed successfully. Actual tool selections were search_catalog, save_reading_item, plan_reading, and plan_reading for the no-match request. Outputs are preserved in live_demo.json and live_demo.txt. Fresh model requests also execute during the primary live recording; its scenario files have the prefix live_video_scenario_. The offline adapter remains a separate execution test, not evidence of language understanding. These examples do not establish reliability for every possible request. No GitHub repository or video-hosting URL was fabricated. The source repository is now public and the live video is hosted on Google Drive with link-viewer access. Actual URLs are recorded in SUBMISSION.md; the final Moodle submission is left to the student.
