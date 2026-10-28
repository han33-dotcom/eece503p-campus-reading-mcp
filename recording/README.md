# Reproduce the offline recording

This optional Windows-only recording harness uses Playwright's browser video capture and Windows SAPI synthesized narration. It is not an extra MCP server or tool. Each scenario button triggers an actual SDK Runner call through the MCP subprocess while the browser is recording. The database is isolated under runtime/recording.

From the project root, after installing the core requirements:

```powershell
.\.venv\Scripts\python.exe -m pip install -r recording/requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe recording/record_demo.py --prepare
.\recording\narrate.ps1
.\.venv\Scripts\python.exe recording/record_demo.py
```

Allow about six minutes for capture and encoding. This overwrites the local demonstration.mp4 and video scenario evidence files. The eight 42-second chapters yield a 5:36 MP4 with narration. Text-only chapter notes and timing are regenerated in DEMONSTRATION.md by --prepare. Browser screenshots, temporary audio, and the isolated demo database stay in runtime/recording and are ignored by Git.

The adapter's tool selections are scripted and all labels disclose offline mode. A real OpenAI model recording must be made separately using agent.py in live mode.

## Reproduce the live recording

Run the same prepare command with `--prepare --live`, regenerate narration with narrate.ps1, and run the capture script with `--live`. Set OPENAI_API_KEY in the process environment first. The live model makes fresh API calls during capture. The primary output is demonstration_live.mp4 and the narration guide is DEMONSTRATION_LIVE.md; the offline recording is preserved. API usage is billable to the configured account. Before capture, two additional live requests smoke-test consecutive calls on the persistent API event loop. The capture then uses a fresh database, so these preflight writes do not appear in the demonstration.
