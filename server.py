#!/usr/bin/env python3
"""
openclaw-face server v2
- HTTP on 7788: serves index.html
- WebSocket on 7789: pushes state events to browser
- Monitors agent session JSONL files for real-time activity
"""

import asyncio
import json
import os
import glob
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

try:
    import websockets
except ImportError:
    print("Missing: pip install websockets")
    raise

# ─── Config ───────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
INDEX_HTML = SCRIPT_DIR / "index.html"
CONFIG_FILE = SCRIPT_DIR / "config.json"
SCAN_INTERVAL = 0.3  # how often we check for file changes


def load_config():
    """Load config.json, falling back to sensible defaults."""
    defaults = {
        "agents_dir": "~/.openclaw/agents",
        "http_port": 7788,
        "ws_port": 7789,
        "agent_names": {},
    }
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                user = json.load(f)
            defaults.update(user)
        except Exception as e:
            print(f"[config] failed to load {CONFIG_FILE}: {e}, using defaults")
    return defaults


CFG = load_config()
HTTP_PORT = CFG["http_port"]
WS_PORT = CFG["ws_port"]
AGENTS_DIR = Path(os.path.expanduser(CFG["agents_dir"]))

# ─── Global state ─────────────────────────────────────────────────────────────

connected_clients: set = set()
broadcast_queue: asyncio.Queue = None


# ─── HTTP Server ──────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            content = INDEX_HTML.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)
        elif path == "/config":
            payload = json.dumps({
                "ws_port": WS_PORT,
                "agent_names": CFG.get("agent_names", {}),
            }, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(payload)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, fmt, *args):
        pass


def run_http_server():
    server = HTTPServer(("127.0.0.1", HTTP_PORT), Handler)
    server.serve_forever()


# ─── WebSocket ────────────────────────────────────────────────────────────────

async def ws_handler(websocket):
    connected_clients.add(websocket)
    await websocket.send(json.dumps({"type": "connected"}))
    try:
        async for _ in websocket:
            pass
    except Exception:
        pass
    finally:
        connected_clients.discard(websocket)


async def broadcaster():
    while True:
        event = await broadcast_queue.get()
        if connected_clients:
            msg = json.dumps(event, ensure_ascii=False)
            await asyncio.gather(
                *[ws.send(msg) for ws in list(connected_clients)],
                return_exceptions=True,
            )


# ─── Session file watcher ─────────────────────────────────────────────────────

def find_session_files():
    """Find all active (non-checkpoint, non-deleted) session JSONL files."""
    pattern = str(AGENTS_DIR / "*/sessions/*.jsonl")
    files = []
    for f in glob.glob(pattern):
        basename = os.path.basename(f)
        if ".checkpoint." in basename or ".deleted." in basename:
            continue
        files.append(f)
    return files


def agent_name_from_path(path: str) -> str:
    """Extract agent name from session file path."""
    # .../agents/<agent-id>/sessions/<uuid>.jsonl
    parts = path.split("/agents/")
    if len(parts) > 1:
        return parts[1].split("/sessions/")[0]
    return "unknown"


def parse_jsonl_line(line: str):
    """Parse a JSONL line and return a face event or None."""
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        return None

    if obj.get("type") != "message":
        return None

    msg = obj.get("message", {})
    role = msg.get("role", "")
    content = msg.get("content", [])

    if role == "user":
        # User message → extract actual text after "[message_id: ...]\nSender: text"
        text = ""
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    raw = block.get("text", "")
                    # Find real message after [message_id: ...]
                    idx = raw.find("[message_id:")
                    if idx != -1:
                        after = raw[idx:]
                        # Skip "[message_id: ...]\n"
                        nl = after.find("\n")
                        if nl != -1:
                            line = after[nl + 1:]
                            # Format: "SenderName: actual message"
                            colon = line.find(": ")
                            if colon != -1:
                                text = line[colon + 2:].strip()[:80]
                            else:
                                text = line.strip()[:80]
                    break
        elif isinstance(content, str):
            text = content[:80]
        if text:
            return {"type": "message_received", "text": text}

    elif role == "assistant":
        # Check what the assistant is doing
        has_tool_call = False
        has_text = False
        text_preview = ""
        stop_reason = msg.get("stopReason", "")

        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "toolCall":
                        has_tool_call = True
                    elif block.get("type") == "text":
                        has_text = True
                        text_preview = block.get("text", "")[:60]

        if has_tool_call:
            return {"type": "thinking", "label": "executing tool…"}
        elif has_text and stop_reason == "stop":
            return {"type": "done", "label": text_preview}
        elif has_text and stop_reason == "toolUse":
            return {"type": "thinking", "label": "using tool…"}

    elif role == "toolResult":
        is_error = msg.get("isError", False)
        if is_error:
            return {"type": "task_error", "label": "tool error"}

    return None


async def session_watcher():
    """Watch session files for new lines and emit events."""
    # Track file positions: path → (inode, offset)
    file_positions: dict[str, tuple[int, int]] = {}

    # Initialize: seek to end of all existing files
    for fpath in find_session_files():
        try:
            stat = os.stat(fpath)
            file_positions[fpath] = (stat.st_ino, stat.st_size)
        except OSError:
            pass

    print(f"[session_watcher] tracking {len(file_positions)} session files")

    last_scan = time.time()
    idle_since = time.time()

    while True:
        await asyncio.sleep(SCAN_INTERVAL)

        # Re-scan for new files every 5 seconds
        now = time.time()
        if now - last_scan > 5:
            for fpath in find_session_files():
                if fpath not in file_positions:
                    try:
                        stat = os.stat(fpath)
                        # New file: start from end (don't replay history)
                        file_positions[fpath] = (stat.st_ino, stat.st_size)
                        print(f"[session_watcher] new file: {os.path.basename(fpath)}")
                    except OSError:
                        pass
            last_scan = now

        # Check each tracked file for new data
        had_activity = False
        for fpath in list(file_positions.keys()):
            try:
                stat = os.stat(fpath)
            except OSError:
                del file_positions[fpath]
                continue

            old_ino, old_offset = file_positions[fpath]

            # File was replaced (different inode)
            if stat.st_ino != old_ino:
                file_positions[fpath] = (stat.st_ino, 0)
                old_offset = 0

            if stat.st_size <= old_offset:
                continue

            # Read new data
            agent = agent_name_from_path(fpath)
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    f.seek(old_offset)
                    new_data = f.read()
                    new_offset = f.tell()
                file_positions[fpath] = (stat.st_ino, new_offset)
            except OSError:
                continue

            # Parse lines
            for line in new_data.strip().split("\n"):
                line = line.strip()
                if not line:
                    continue
                event = parse_jsonl_line(line)
                if event:
                    event["agent"] = agent
                    had_activity = True
                    idle_since = now
                    print(f"[{agent}] {event['type']}: {event.get('label', event.get('text', ''))[:40]}")
                    await broadcast_queue.put(event)

        # If idle for 10+ seconds after activity, send idle
        if had_activity is False and (now - idle_since) > 10:
            idle_since = now + 9999  # prevent spamming idle


# ─── Main ─────────────────────────────────────────────────────────────────────

async def main():
    global broadcast_queue
    broadcast_queue = asyncio.Queue()

    t = threading.Thread(target=run_http_server, daemon=True)
    t.start()

    print(f"[openclaw-face] HTTP  → http://localhost:{HTTP_PORT}")
    print(f"[openclaw-face] WS    → ws://localhost:{WS_PORT}")
    print(f"[openclaw-face] Agents → {AGENTS_DIR}")
    print()

    async with websockets.serve(ws_handler, "127.0.0.1", WS_PORT):
        await asyncio.gather(
            broadcaster(),
            session_watcher(),
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[openclaw-face] bye")
