# OpenClaw Dynamic Island

macOS Dynamic Island style widget for [OpenClaw](https://github.com/nicepkg/openclaw) — shows real-time AI agent status on your desktop.

![preview](https://img.shields.io/badge/macOS-13%2B-blue) ![license](https://img.shields.io/badge/license-MIT-green)

## What it does

A translucent, frosted-glass pill floats at the top center of your screen, just like iPhone's Dynamic Island. It monitors OpenClaw agent session files and displays live status:

| State | Emoji | Meaning |
|-------|-------|---------|
| Sleeping | `😴` | Not connected |
| Idle | `😊` | Ready, waiting |
| Alert | `👀` | Message received |
| Thinking | `🤔` | Processing / tool call |
| Done | `😄` | Task completed (window shakes!) |
| Error | `😰` | Something went wrong |

When multiple agents are running, the agent name is shown next to the status.

## Requirements

- macOS 13+
- Python 3.9+
- Swift (comes with Xcode Command Line Tools)

```bash
# Install Xcode Command Line Tools (if not already)
xcode-select --install

# Install Python dependency
pip3 install websockets
```

## Quick Start

```bash
# 1. Clone
git clone https://github.com/nicepkg/openclaw-dynamic-island.git
cd openclaw-dynamic-island

# 2. Configure
cp config.example.json config.json
# Edit config.json — set your agents directory and agent names

# 3. Run
./start.sh
```

The Dynamic Island will appear at the top center of your screen.

To stop:

```bash
./start.sh stop
```

## Configuration

Edit `config.json`:

```json
{
  "agents_dir": "~/.openclaw/agents",
  "http_port": 7788,
  "ws_port": 7789,
  "agent_names": {
    "my-agent-id": "My Bot",
    "another-agent": "Group Chat"
  }
}
```

| Field | Description | Default |
|-------|-------------|---------|
| `agents_dir` | Path to OpenClaw agents directory | `~/.openclaw/agents` |
| `http_port` | HTTP server port | `7788` |
| `ws_port` | WebSocket port | `7789` |
| `agent_names` | Map agent IDs to friendly display names | `{}` |

## Auto-start on Login

```bash
# Install Launch Agent
sed "s|__INSTALL_DIR__|$(pwd)|g" com.openclaw.face.plist > ~/Library/LaunchAgents/com.openclaw.face.plist
launchctl load ~/Library/LaunchAgents/com.openclaw.face.plist

# Uninstall
launchctl unload ~/Library/LaunchAgents/com.openclaw.face.plist
rm ~/Library/LaunchAgents/com.openclaw.face.plist
```

## Architecture

```
server.py       — Watches agent session JSONL files, pushes events via WebSocket
index.html      — Renders emoji face + status (also serves as the widget UI)
widget.swift    — Native macOS pill window (NSPanel + frosted glass + WKWebView)
start.sh        — Start/stop helper script
config.json     — Your local configuration (git-ignored)
```

## How it Works

1. `server.py` watches `~/.openclaw/agents/*/sessions/*.jsonl` for new lines
2. Parses each line to detect state changes (message received, thinking, done, error)
3. Broadcasts events to connected WebSocket clients
4. `widget.swift` creates a floating NSPanel with frosted glass effect
5. Loads `index.html?widget` in a transparent WKWebView inside the pill
6. The page connects via WebSocket and updates emoji/status in real-time
7. On task completion, JS tells Swift to physically shake the window

## License

MIT
