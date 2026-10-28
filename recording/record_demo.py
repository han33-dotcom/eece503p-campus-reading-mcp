"""Record real browser execution of offline Agents SDK/MCP scenarios."""
import asyncio
import contextlib
import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT
SCRATCH = PROJECT / "runtime/recording"
SCRATCH.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(PROJECT))
os.environ["LIBRARY_DB"] = str(SCRATCH / f"demo_{int(time.time())}.sqlite3")
from agent import connect, SCENARIOS, INSTRUCTIONS
from offline_model import ScriptedDemoModel
from agents import Agent, Runner, RunConfig
LIVE = '--live' in sys.argv

CHAPTERS = [
 {"title":"Campus Reading Toolkit", "subtitle":"EECE503P / C5 Agent Tools / Hassan Nasrallah",
  "notes":["Exactly three MCP tools", "Data: search_catalog", "Action: save_reading_item", "Orchestration: plan_reading"],
  "code":"python agent.py --offline\n\nReal SDK Runner + real stdio MCP\nScripted model adapter: no OpenAI API call\nLocal catalogue fixture + durable SQLite writes",
  "narration":"This is Campus Reading, a small MCP toolkit for the Agent Tools assignment. It contains exactly one data tool, one action tool, and one orchestration tool. The data tool searches a demonstration library catalogue. The action tool saves a known book to a persistent reading list. The orchestration tool finds a match and saves it. This recording uses an explicitly scripted model adapter because no funded OpenAI API key is configured. The Agents SDK, MCP connection, server execution, and database effects are real. This is an offline integration demonstration, not a live language model evaluation."},
 {"title":"One host, one client, one server", "subtitle":"Capability discovery precedes execution",
  "notes":["Host: Python Agent + Runner", "Client: MCPServerStdio inside the SDK", "Server: independent FastMCP subprocess", "Typed input and output schemas"],
  "code":"async with MCPServerStdio(params={\n    'command': sys.executable,\n    'args': [absolute_server_path]\n}) as server:\n    tools = await server.list_tools()\n    agent = Agent(mcp_servers=[server], ...)\n    result = await Runner.run(agent, prompt)",
  "narration":"The Python application acts as the host. It owns the user request, the agent configuration, and the model choice. Inside that host, the SDK's MCP Server Stdio object manages the protocol client. It starts a separate FastMCP server process and communicates over standard input and output. Tool discovery returns descriptions and JSON schemas. The Runner executes the selected capability and passes its actual result back to the model adapter. The offline adapter only decides the predefined call. It does not bypass the client, server, or storage. In live mode, an OpenAI model makes that selection."},
 {"title":"01 / Data tool", "subtitle":"Read information without changing state", "scenario":0,
  "notes":["Query: artificial intelligence", "Case-insensitive all-word matching", "Expected matches: B001 and B004", "No database is created by lookup"],
  "code":"@mcp.tool(annotations={'readOnlyHint': True})\ndef search_catalog(query: str, limit: int = 5)\n    -> SearchResult:\n    return library.search_catalog(query, limit)",
  "narration":"Now the browser triggers a real SDK run with the request, find books about artificial intelligence. The scripted adapter emits search catalog, and the SDK routes that invocation through MCP to the server. The result contains two catalogue records, B zero zero one and B zero zero four. Search matches all query words across the title, author, and subjects, ignoring case. The tool has a structured result containing the query, count, and books. The database state below shows that no database exists yet. This verifies the read only boundary. A blank query produces a clear invalid query error."},
 {"title":"02 / Action tool", "subtitle":"Persist a known book, with a reusable receipt", "scenario":1,
  "notes":["Explicit request: save B003", "SQLite primary key: list_name + book_id", "Duplicate calls return already_saved", "Unknown book IDs fail before any write"],
  "code":"INSERT OR IGNORE INTO reading_items\n    VALUES (list_name, book_id, saved_at)\n\nSaveResult(status, list_name, book, saved_at)\n# The original timestamp survives retries.",
  "narration":"The next request explicitly asks to save book B zero zero three to the course list. The action tool validates that the ID exists and that the list label is valid. It then performs a real SQLite insert and returns a receipt with the title, status, list name, and timestamp. The database panel now contains one row. A composite primary key prevents duplicate entries. Repeating the same save returns already saved and preserves the original timestamp. This matters because an agent or client may retry a request. An unknown book ID is rejected instead of creating an invalid reading list entry."},
 {"title":"03 / Orchestration tool", "subtitle":"One higher-level request, two ordered domain steps", "scenario":2,
  "notes":["Explicit request: find a book about agents and save it", "Step 1: search_catalog", "Step 2: save_reading_item", "Selection: lowest matching book_id"],
  "code":"found = search_catalog(query, limit=10)\nif not found.books:\n    raise LibraryError('NO_MATCH')\nsaved = save_reading_item(\n    found.books[0].book_id, list_name)\nreturn PlanResult(steps=[...], saved=saved)",
  "narration":"Here the request asks to find a book about agents and save it. The SDK calls the orchestration tool once through MCP. Inside that tool, the search function runs first, followed by the save function. These are the same domain implementations used by the two primitive tools, so validation and persistence rules stay consistent. There are two matching books. The documented rule chooses the lowest book ID, B zero zero one. The combined result reports the match count, both step names, and the actual save receipt. The database now has two entries. These internal steps are not separate network calls."},
 {"title":"04 / Predictable failure", "subtitle":"A failed plan must never invent a successful save", "scenario":3,
  "notes":["Query: quantum gardening", "No matching catalogue record", "MCP tool error: NO_MATCH", "Database still contains exactly two rows"],
  "code":"if not found.books:\n    raise LibraryError(\n      'NO_MATCH: No book matched; '\n      'try fewer words. Nothing was saved.')\n\n# Server converts this to a ToolError.",
  "narration":"For the failure case, the request asks for a book about quantum gardening. Nothing matches the fixture catalogue. The orchestration stops before the save function and returns a no match error. That error travels back through MCP to the SDK, and the offline adapter reports the actual returned content. The database remains at two rows, so failure does not create a phantom entry. The distinction is useful: an empty result is valid for a simple search, but it prevents an orchestration whose goal requires a save. Tests also cover invalid inputs, unknown books, unavailable catalogue data, and storage failures."},
 {"title":"Verification and design tradeoffs", "subtitle":"Test effects and interfaces across process boundaries",
  "notes":["18 automated tests passed", "Exact tool count + input/output schemas", "Separate server process + restart persistence", "Scripted SDK run verifies execution, not LLM selection"],
  "code":"python -m pytest -q\n\n18 passed\n\nUnit checks + actual stdio MCP checks\nOrchestration call order verified with spies\nSQLite state checked independently",
  "narration":"The verification suite contains eighteen passing tests. It checks the single purpose domain behavior, predictable failures, durable storage, and duplicate handling. A subprocess integration test discovers exactly three tools, checks their schemas, calls them through MCP, and restarts the server to confirm persistence. Another test runs the real Agents SDK Runner with the offline adapter. Function spies verify that orchestration calls search before save. These checks establish that the implementation works across the protocol boundary. They do not establish that a live language model selects the correct tool. That separate evaluation requires the configured API key."},
 {"title":"Reflection and submission", "subtitle":"Three clear boundaries; one reproducible local package",
  "notes":["Lookup reads; action persists; orchestration coordinates", "Local fixture avoids unrelated service dependencies", "Next: real catalogue + user-specific storage", "Before final submission: live-model recording + hosted links"],
  "code":"Included:\n  server.py / library.py / agent.py\n  README / pinned dependencies / tests\n  SUMMARY.md / REFLECTION.md\n  evidence / this narrated recording\n\nLive mode: python agent.py --chat",
  "narration":"The main design decision was to draw boundaries around observable effects. Search only retrieves data, save persists one known item, and the planner owns the combined workflow. Three tools are enough for this focused example, though a real application would also need list inspection and removal. Future work would connect a real library catalogue, add user isolation, and improve selection beyond the lowest ID rule. The package includes source code, setup instructions, tests, the reading summary, reflection, and evidence. This local recording uses synthesized narration and an offline adapter. A live model recording and hosted repository and video links remain separate final submission steps."}
]

if LIVE:
    CHAPTERS[0]['code'] = 'python agent.py\n\nLive OpenAI model: gpt-4.1-mini\nReal SDK Runner + real stdio MCP\nLocal catalogue fixture + durable SQLite writes'
    CHAPTERS[0]['narration'] = 'This is Campus Reading, an MCP toolkit for the Agent Tools assignment. It contains exactly one data tool, one action tool, and one orchestration tool. Search retrieves books from a small demonstration catalogue. Save adds a known book to a persistent reading list. Plan reading combines those operations. This recording uses a live OpenAI model through the OpenAI Agents SDK. The model chooses its tool calls from the descriptions discovered over MCP. The browser will trigger fresh requests during this recording. Tool execution, returned results, and database effects are real.'
    CHAPTERS[1]['narration'] = 'The Python application is the MCP host. It owns the user request, agent instructions, and model configuration. The SDK MCP Server Stdio object manages the client connection to a separate FastMCP subprocess. The client discovers exactly three tools, with descriptions and input and output schemas. The Runner sends the available tools to the live model. When the model selects a tool, the SDK invokes it through MCP, receives the result, and asks the model for its response. The protocol connects the components; the model makes the language based routing decision.'
    CHAPTERS[2]['narration'] = 'The browser now submits a fresh request to find books about artificial intelligence. The live model selects search catalog, and the SDK sends that invocation through the MCP client to the server. Search uses case insensitive matching across the title, author, and subjects. It returns two matching records with IDs B zero zero one and B zero zero four. The assistant response below is generated from that actual result. The independent database panel shows that no database exists yet. This verifies that the data tool retrieves information without changing the reading list.'
    CHAPTERS[3]['narration'] = 'The next request explicitly asks the live model to save B zero zero three to the course list. The model selects save reading item. The server validates that the book exists and the list label is valid, then inserts a row into SQLite. Its receipt reports the actual status, book, list, and timestamp. The database panel independently confirms one saved row. A uniqueness constraint makes this operation idempotent: repeating the same book and list pair returns already saved, preserving the original timestamp. Unknown IDs fail before writing. This tool has one observable effect: persisting a known item.'
    CHAPTERS[4]['narration'] = 'This request asks to find a book about agents and save it. The live model selects the orchestration tool, plan reading. One MCP invocation reaches the server. Inside that operation, the same search function used by the data tool runs first, followed by the same save function used by the action tool. Two books match, and the documented selection rule chooses the lowest book ID. The result reports both internal steps and a real save receipt. The database now contains two entries. This separates the model choosing a higher level capability from the deterministic workflow inside the server.'
    CHAPTERS[5]['narration'] = 'Now the live model receives a request for a book about quantum gardening. The catalogue has no match, so the planner stops before saving and returns a clear no match error. The actual error travels back through the MCP client to the Runner. The model then explains the failure to the user instead of inventing a successful save. The independent database check still shows two rows. An empty result is valid for a data lookup, but it prevents a workflow whose goal requires saving a matching book. Tests also cover invalid inputs, unknown IDs, catalogue failures, and storage errors.'
    CHAPTERS[6]['notes'][-1] = 'Live model selects tools; independent checks verify effects'
    CHAPTERS[6]['narration'] = 'Eighteen automated tests passed. They verify domain behavior, predictable failures, duplicate handling, and persistent storage. The subprocess test discovers exactly three tools, checks their schemas, calls them over MCP, and restarts the server to verify persistence. Function spies check that orchestration runs search before save. An offline SDK adapter remains available for reproducible testing without API charges. Separately, the live model scenario suite selected all three tools successfully. The recording adds fresh live requests and preserves their outputs. These are focused examples, not an exhaustive evaluation of every possible user request.'
    CHAPTERS[7]['notes'][-1] = 'Live-model evidence included; publish repository and video links'
    CHAPTERS[7]['narration'] = 'The boundaries follow observable effects: lookup reads information, action persists one item, and orchestration coordinates the combined request. Three tools are enough for this focused demonstration. A larger application would need list inspection, removal, a real catalogue service, and user specific storage. The written summary critiques the reference Fetch server and explains the MCP host, client, and server roles. The submission includes source code, configuration, tests, reflection, and this live recording. Repository and video hosting links still need publication to the chosen accounts. The local package does not invent external URLs or include an API key.'

HTML = r'''<!doctype html><meta charset="utf-8"><title>Campus Reading / MCP Demo</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#0b1220;color:#e4edf8;font:20px 'Segoe UI',sans-serif}
header{padding:22px 40px;border-bottom:1px solid #26354b;display:flex;justify-content:space-between;color:#73d6cb;font-size:16px;letter-spacing:2px}
main{padding:24px 40px}h1{font-size:42px;margin:0 0 8px}h2{font-size:19px;color:#9cacc5;font-weight:400;margin:0 0 22px}
.grid{display:grid;grid-template-columns:0.85fr 1.25fr;gap:26px}.card{background:#121e30;border:1px solid #2a3b54;border-radius:14px;padding:22px}
ul{padding-left:24px;margin:0 0 18px}li{margin-bottom:12px;line-height:1.45}pre{font:17px/1.5 Consolas,monospace;white-space:pre-wrap;overflow-wrap:anywhere;margin:0;color:#b7d7fc}
.tag{font-size:14px;color:#f5c971;margin-bottom:15px;letter-spacing:1px}.muted{font-size:14px;color:#99acc4;margin-top:14px}
#trace{font-size:16px;line-height:1.42;max-height:360px;overflow:hidden}#db{color:#7adfbd;margin-top:18px;font-size:16px}
button{background:#72dfc8;color:#102334;border:0;border-radius:8px;padding:10px 20px;font-weight:700;margin-bottom:14px;cursor:pointer}
footer{position:fixed;bottom:0;width:100%;padding:14px 40px;background:#101b2b;color:#99acc4;font-size:14px;display:flex;justify-content:space-between}#bar{position:fixed;bottom:0;left:0;height:4px;background:#72dfc8;width:0}
</style>
<header><span>CAMPUS READING / MCP TOOLKIT</span><span>OFFLINE MODEL ADAPTER · REAL SDK + MCP</span></header>
<main><h1 id="title"></h1><h2 id="subtitle"></h2><div class="grid"><div class="card"><div class="tag">DESIGN / CONTRACT</div><ul id="notes"></ul><pre id="code"></pre></div>
<div class="card"><div class="tag" id="righttag">EXECUTION / EVIDENCE</div><button id="run" hidden>Run SDK → MCP scenario</button><pre id="trace">Preparing demonstration...</pre><pre id="db"></pre></div></div></main>
<footer><span>Hassan Nasrallah / EECE503P / C5 Agent Tools</span><span id="chapter"></span></footer><div id="bar"></div>
<script>
let current=0;let chapters=[];
async function show(i){current=i;const c=chapters[i];title.textContent=c.title;subtitle.textContent=c.subtitle;notes.replaceChildren(...c.notes.map(n=>{let e=document.createElement('li');e.textContent=n;return e}));code.textContent=c.code;chapter.textContent=`${i+1} / ${chapters.length}`;document.getElementById('bar').style.width=((i+1)/chapters.length*100)+'%';db.textContent='';trace.textContent=c.scenario===undefined ? (i===0 ? 'Three capabilities.\nOne standard protocol.\nA small, testable workflow.\n\nNo live OpenAI API request occurs\nin this recording.' : i===1 ? 'User request\n   ↓\nHost: Agent + Runner\n   ↓\nClient: MCPServerStdio\n   ↓ stdio JSON-RPC\nServer: FastMCP\n   ↓\nCatalogue / SQLite\n   ↑ structured result' : i===6 ? 'Captured test result:\n18 passed in 14.06s\n\nSee evidence/tests.txt for the\nfinal reproducible test log.\n\nDatabase effects are checked\nindependently of assistant text.' : 'Local deliverables are complete.\n\nExternal steps still required:\n- Run with a funded OpenAI API key\n- Record live model tool selection\n- Publish repository and recording\n\nNo hosted URLs are fabricated.') : 'Ready. The button below runs\nthe actual SDK and MCP subprocess.';run.hidden=c.scenario===undefined;run.disabled=false;}
run.onclick=async()=>{run.disabled=true;trace.textContent='Running Agent → SDK client → MCP server...';const r=await fetch('/scenario/'+chapters[current].scenario);const d=await r.json();trace.textContent=d.display;db.textContent=d.database;};
fetch('/chapters').then(r=>r.json()).then(c=>{chapters=c;show(0)});
</script>'''


if LIVE:
    HTML = HTML.replace('OFFLINE MODEL ADAPTER · REAL SDK + MCP', 'LIVE OPENAI MODEL · AGENTS SDK + MCP')
    HTML = HTML.replace('No live OpenAI API request occurs\\nin this recording.', 'Live model: gpt-4.1-mini\\nFresh API requests execute during recording.')
    HTML = HTML.replace('- Run with a funded OpenAI API key\\n- Record live model tool selection\\n- Publish repository and recording', '- Publish repository and recording\\n- Insert actual hosted submission links')
    HTML = HTML.replace('max-height:360px', 'max-height:490px')

async def execute(index):
    prompt, name, args = SCENARIOS[index]
    async with connect() as server:
        tools = await server.list_tools()
        agent = Agent(name="Campus Reading", instructions=INSTRUCTIONS,
                      model=os.environ.get('OPENAI_MODEL', 'gpt-4.1-mini') if LIVE else ScriptedDemoModel(name, args), mcp_servers=[server])
        result = await Runner.run(agent, prompt, run_config=RunConfig(tracing_disabled=True))
        actual = next(item.output for item in result.new_items if item.type == "tool_call_output_item")
        text = str(actual)
        tool_call = next(item.raw_item for item in result.new_items if item.type == 'tool_call_item')
        name, args = tool_call.name, json.loads(tool_call.arguments)
        # The SDK output contains JSON-encoded text content blocks. Parse the
        # real result for readable display; preserve the full original evidence.
        try:
            outer = actual if isinstance(actual, (dict, list)) else json.loads(text)
            inner = outer[0]['text'] if isinstance(outer, list) else outer['text']
            try:
                value = json.loads(inner)
            except ValueError:
                value = inner
        except (ValueError, KeyError, TypeError):
            value = text
        record = {"mode":"live OpenAI model" if LIVE else "offline scripted adapter", "prompt":prompt,
                  "discovered_tools":[t.name for t in tools], "tool":name,
                  "arguments":args, "actual_output":text, "final_output":result.final_output}
        prefix = 'live_video' if LIVE else 'video'
        (PROJECT / "evidence" / f"{prefix}_scenario_{index+1}.json").write_text(
            json.dumps(record, indent=2), encoding="utf-8")
        display = "USER: " + prompt + "\n\nSDK → MCP tools/call\n" + name + "(" + json.dumps(args) + ")\n\nMCP → SDK actual result\n"
        if isinstance(value, dict) and "books" in value:
            display += f"count: {value['count']}\n" + "\n".join(b["book_id"]+" / "+b["title"] for b in value["books"])
        elif isinstance(value, dict) and "saved" in value:
            s = value["saved"]
            display += f"matches: {value['matches']}\nsteps: {' → '.join(value['steps'])}\nselection: {value['selection_rule']}\nstatus: {s['status']}\nbook: {s['book']['book_id']} / {s['book']['title']}\nlist: {s['list_name']}"
        elif isinstance(value, dict) and "status" in value:
            display += f"status: {value['status']}\nbook: {value['book']['book_id']} / {value['book']['title']}\nlist: {value['list_name']}\nsaved_at: {value['saved_at']}"
        else:
            display += str(value)
        db = Path(os.environ["LIBRARY_DB"])
        if db.exists():
            with sqlite3.connect(db) as conn:
                rows = conn.execute("SELECT list_name, book_id FROM reading_items ORDER BY book_id").fetchall()
            database = f"INDEPENDENT SQLITE CHECK / {len(rows)} row(s)\n" + "\n".join(f"{l} / {b}" for l,b in rows)
        else:
            database = "INDEPENDENT SQLITE CHECK\nDatabase does not exist. Lookup made no write."
        if LIVE:
            display += '\n\nLIVE ASSISTANT\n' + str(result.final_output)
        return {"display":display,"database":database}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/scenario/'):
            data = asyncio.run_coroutine_threadsafe(
                execute(int(self.path.rsplit('/',1)[-1])), API_LOOP).result(timeout=90)
            body, content = json.dumps(data).encode(), 'application/json'
        elif self.path == '/chapters':
            body, content = json.dumps(CHAPTERS).encode(), 'application/json'
        else:
            body, content = HTML.encode(), 'text/html; charset=utf-8'
        self.send_response(200)
        self.send_header('Content-Type', content)
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *args):
        pass


async def record():
    from playwright.async_api import async_playwright
    from imageio_ffmpeg import get_ffmpeg_exe
    global API_LOOP
    API_LOOP = asyncio.new_event_loop()
    threading.Thread(target=API_LOOP.run_forever, daemon=True).start()
    if LIVE:
        # The OpenAI SDK caches its async client. Keep one event loop alive for
        # all HTTP handlers, and smoke-test repeated calls before recording.
        for index in (0, 1):
            await asyncio.wrap_future(asyncio.run_coroutine_threadsafe(execute(index), API_LOOP))
        os.environ['LIBRARY_DB'] = str(SCRATCH / f'capture_{int(time.time())}.sqlite3')
        print('Preflight passed: consecutive live SDK requests on one persistent loop.', flush=True)
    httpd = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    # SAPI narration was generated before recording, one WAV per chapter.
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport={"width":1600,"height":900},
                                            record_video_dir=str(SCRATCH / 'capture'),
                                            record_video_size={"width":1600,"height":900})
        page = await context.new_page()
        await page.goto(f'http://127.0.0.1:{httpd.server_port}')
        await page.wait_for_function('chapters.length === 8')
        print('Recording started: 8 chapters, 42 seconds each.', flush=True)
        for i,c in enumerate(CHAPTERS):
            started = time.monotonic()
            await page.evaluate('i => show(i)', i)
            if 'scenario' in c:
                await asyncio.sleep(2)
                await page.get_by_role('button').click()
                await page.wait_for_function("document.getElementById('db').textContent.length > 0", timeout=45000)
            await page.screenshot(path=str(SCRATCH / f'chapter_{i+1}.png'))
            print(f'Chapter {i+1}/8 captured: {c["title"]}', flush=True)
            await asyncio.sleep(max(0,42-(time.monotonic()-started)))
        video = page.video
        await context.close()
        raw = await video.path()
        await browser.close()
    httpd.shutdown()
    ffmpeg = get_ffmpeg_exe()
    # Pad each narration segment to 42 seconds for chapter alignment.
    segments=[]
    for i in range(8):
        segment=SCRATCH / f'audio_{i}.wav'
        subprocess.run([ffmpeg,'-y','-i',str(SCRATCH/f'narration_{i}.wav'),
                        '-af','apad','-t','42','-ar','44100','-ac','1',str(segment)],
                       check=True, stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        segments.append(segment)
    import wave
    with wave.open(str(SCRATCH / 'narration.wav'),'wb') as target:
        for i,segment in enumerate(segments):
            with wave.open(str(segment),'rb') as source:
                if i==0: target.setparams(source.getparams())
                target.writeframes(source.readframes(source.getnframes()))
    subprocess.run([ffmpeg,'-y','-i',str(raw),'-i',str(SCRATCH/'narration.wav'),
                    '-t','336','-c:v','libx264','-preset','fast','-crf','23','-pix_fmt','yuv420p',
                    '-c:a','aac','-b:a','96k','-movflags','+faststart',str(PROJECT/('demonstration_live.mp4' if LIVE else 'demonstration.mp4'))],
                   check=True, stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    print('Saved live recording.' if LIVE else 'Saved offline recording.',flush=True)


if __name__ == '__main__':
    if '--prepare' in sys.argv:
        for i,c in enumerate(CHAPTERS):
            (SCRATCH / f'narration_{i}.txt').write_text(c['narration'],encoding='utf-8')
        (PROJECT/('DEMONSTRATION_LIVE.md' if LIVE else 'DEMONSTRATION.md')).write_text(
            '# Demonstration recording\n\nDuration: 5 minutes 36 seconds. Automated browser capture with synthesized narration.\n\n'
            '**Scope:** The model adapter is scripted. SDK Runner calls, MCP subprocess requests, tool results, '
            'errors, and SQLite effects execute during the recording. This is not a live OpenAI model recording.\n\n'
            'The browser console is a local recording harness, not an extra MCP tool. Four scenario JSON files '
            'in evidence/ preserve actual outputs from the recording.\n\n'
            + '\n\n'.join(f'## {i*42//60:02d}:{i*42%60:02d} - {c["title"]}\n\n{c["narration"]}' for i,c in enumerate(CHAPTERS))
            + '\n\n## Live-model replacement\n\nConfigure OPENAI_API_KEY and run `python agent.py --chat`. '
            'Use the four prompts in README.md. Show source code and the database, introduce all three '
            'categories, discuss failures and reflection, and record 5-7 minutes. Publish code and video '
            'to your chosen accounts and insert actual URLs into SUBMISSION.md.\n', encoding='utf-8')
        if LIVE:
            target = PROJECT / 'DEMONSTRATION_LIVE.md'
            content = target.read_text(encoding='utf-8')
            start = content.index('**Scope:**')
            end = content.index('## 00:00')
            content = content[:start] + '**Scope:** Live gpt-4.1-mini model calls through the OpenAI Agents SDK and a real stdio MCP server. Tool selection is performed by the model. Four fresh requests execute during browser capture. Narration is synthesized. Actual outputs are preserved in evidence/live_video_scenario_1.json through live_video_scenario_4.json.\n\n' + content[end:]
            content = content.split('## Live-model replacement')[0]
            target.write_text(content, encoding='utf-8')
    else:
        asyncio.run(record())
