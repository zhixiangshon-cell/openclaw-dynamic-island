# 🏝️ OpenClaw Dynamic Island

> **macOS 桌面 AI 状态监控小组件** — 为 [OpenClaw](https://github.com/nicepkg/openclaw) 打造的 Dynamic Island 风格实时多 Agent 状态显示工具。毛玻璃药丸窗口悬浮在屏幕顶部，5 种状态自动切换，支持多 Agent 同时管理。

![macOS 13+](https://img.shields.io/badge/macOS-13%2B-blue) ![MIT License](https://img.shields.io/badge/license-MIT-green) ![OpenClaw compatible](https://img.shields.io/badge/OpenClaw-compatible-orange) ![ClawHub](https://img.shields.io/badge/ClawHub-available-purple) ![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue) ![Swift 5+](https://img.shields.io/badge/Swift-5%2B-orange)

---

## What is OpenClaw Dynamic Island?

**OpenClaw Dynamic Island** is a macOS desktop widget that brings iPhone-style Dynamic Island UI to your Mac. It monitors [OpenClaw](https://github.com/nicepkg/openclaw) AI agent session files in real-time and displays live status with a frosted glass pill window floating at the top center of your screen.

Designed for developers and teams running multiple AI agents, it provides instant visibility into agent states — idle, thinking, completing tasks, or encountering errors — all without switching windows.

## Quick Start

### Option 1: ClawHub Install (Recommended)

```bash
openclaw skills install dynamic-island
```

Or using the ClawHub CLI:

```bash
npx clawhub@latest install dynamic-island
```

Then run the one-click setup:

```bash
cd ~/.openclaw/skills/dynamic-island
bash setup.sh
./start.sh
```

### Option 2: Manual Install

```bash
# 1. Clone
git clone https://github.com/zhixiangshon-cell/openclaw-dynamic-island.git
cd openclaw-dynamic-island

# 2. Install dependency
pip3 install websockets

# 3. Configure
cp config.example.json config.json
# Edit config.json — set your agent names

# 4. Run
./start.sh
```

Stop with `./start.sh stop`.

## Key Features

| Feature | Description |
|---------|-------------|
| **Real-time Status** | 5 states: Idle, Alert, Thinking, Done, Error — auto-switching based on agent activity |
| **Multi-Agent** | Monitor all your OpenClaw agents simultaneously in one pill |
| **Hover to Expand** | Mouse hover expands the pill to show full agent list with latest 2 messages per agent |
| **Feishu Integration** | Click an agent name to open its Feishu (Lark) chat directly |
| **Sound Effects** | Glass sound on task completion, bass sound on error |
| **emolog Icons** | Custom cute emoji icons powered by [emolog](https://apps.apple.com/app/emolog/id6443809191) |
| **Cursor Highlight** | Agent group highlights as your cursor moves over it |
| **Auto-start** | LaunchAgent support for boot startup |
| **Frosted Glass** | Native macOS NSVisualEffectView for authentic glass effect |
| **Non-intrusive** | Borderless, non-activating panel — never steals focus |

## Status Icons

| State | Icon | Meaning |
|-------|------|---------|
| Idle | ![idle](emolog/idle.png) | Agent ready, waiting for tasks |
| Alert | ![alert](emolog/alert.png) | New message received |
| Thinking | ![thinking](emolog/thinking.png) | Processing / tool call in progress |
| Done | ![done](emolog/done.png) | Task completed — window shakes + glass sound |
| Error | ![error](emolog/error.png) | Something went wrong — bass sound alert |

> Icons powered by [emolog](https://apps.apple.com/app/emolog/id6443809191).

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
  },
  "agent_links": {
    "my-agent-id": "lark://applink.feishu.cn/client/chat/open?openId=xxx"
  }
}
```

| Field | Description | Default |
|-------|-------------|---------|
| `agents_dir` | Path to OpenClaw agents directory | `~/.openclaw/agents` |
| `http_port` | HTTP server port | `7788` |
| `ws_port` | WebSocket port | `7789` |
| `agent_names` | Map agent IDs to display names | `{}` |
| `agent_links` | Map agent IDs to Feishu chat URLs (clickable) | `{}` |

## Auto-start on Login

```bash
sed "s|__INSTALL_DIR__|$(pwd)|g" com.openclaw.face.plist > ~/Library/LaunchAgents/com.openclaw.face.plist
launchctl load ~/Library/LaunchAgents/com.openclaw.face.plist

# Uninstall
launchctl unload ~/Library/LaunchAgents/com.openclaw.face.plist
rm ~/Library/LaunchAgents/com.openclaw.face.plist
```

## Architecture

```
setup.sh        — One-click setup (env check + compile + config)
start.sh        — Start/stop helper script
server.py       — Watches agent session JSONL files, pushes events via WebSocket
index.html      — Renders emolog icons + multi-agent UI (widget + expanded view)
widget.swift    — Native macOS pill window (NSPanel + frosted glass + hover detection)
emolog/         — Custom emolog icons (idle, alert, thinking, done, error)
config.json     — Your local configuration (git-ignored)
```

## How it Works

1. `server.py` watches `~/.openclaw/agents/*/sessions/*.jsonl` for new lines
2. Parses each line to detect state changes (message received, thinking, done, error)
3. Broadcasts events to connected WebSocket clients
4. `widget.swift` creates a floating NSPanel with frosted glass effect
5. Loads `index.html?widget` in a transparent WKWebView inside the pill
6. The page connects via WebSocket and updates emolog icons/status in real-time
7. On task completion, JS tells Swift to physically shake the window + play sound
8. Hover over the pill to expand and see all agents with recent messages
9. Swift HoverView tracks mouse position and highlights the agent group under cursor

## Requirements

- macOS 13+
- Python 3.9+
- Swift (comes with Xcode Command Line Tools)
- [OpenClaw](https://github.com/nicepkg/openclaw) running with agents

---

## 中文说明

### 这是什么？

**OpenClaw Dynamic Island** 是一个 macOS 桌面小组件，把 iPhone 灵动岛的交互体验搬到了 Mac 上。它实时监控 OpenClaw AI Agent 的会话文件，在屏幕顶部显示一个毛玻璃药丸窗口，自动切换 5 种状态。

专为同时运行多个 AI Agent 的开发者和团队设计，不用切窗口就能一眼看到所有 Agent 在干嘛。

### 安装方式

**方式一：ClawHub 安装（推荐）**

```bash
openclaw skills install dynamic-island
cd ~/.openclaw/skills/dynamic-island
bash setup.sh
./start.sh
```

**方式二：手动安装**

```bash
git clone https://github.com/zhixiangshon-cell/openclaw-dynamic-island.git
cd openclaw-dynamic-island
pip3 install websockets
cp config.example.json config.json
./start.sh
```

### 核心功能

| 功能 | 说明 |
|------|------|
| **实时状态** | 5 种状态自动切换：待命、收到消息、思考中、搞定了、出错了 |
| **多 Agent** | 同时管理所有 OpenClaw Agent |
| **悬停展开** | 鼠标悬停展开 Agent 列表，显示最近 2 条对话 |
| **飞书集成** | 点击 Agent 名字直接打开飞书聊天 |
| **音效提示** | 任务完成玻璃音、出错低音提示 |
| **emolog 图标** | 可爱的自定义表情图标 |
| **光标高亮** | 鼠标移到哪个 Agent 哪个就高亮 |
| **开机自启** | LaunchAgent 支持开机自动启动 |

### 状态图标

| 状态 | 图标 | 含义 |
|------|------|------|
| 待命 | ![idle](emolog/idle.png) | Agent 就绪，等待任务 |
| 收到消息 | ![alert](emolog/alert.png) | 收到新消息 |
| 思考中 | ![thinking](emolog/thinking.png) | 正在处理 / 调用工具 |
| 搞定了 | ![done](emolog/done.png) | 任务完成，药丸晃动 + 玻璃音效 |
| 出错了 | ![error](emolog/error.png) | 出错了，低音提示 |

### 配置说明

编辑 `config.json`：

```json
{
  "agents_dir": "~/.openclaw/agents",
  "agent_names": {
    "my-agent-id": "我的 Bot"
  },
  "agent_links": {
    "my-agent-id": "lark://applink.feishu.cn/client/chat/open?openId=xxx"
  }
}
```

- `agent_names`：给 Agent 取一个好认的显示名
- `agent_links`：配了就能点击跳转飞书聊天（可选）

---

## License

MIT
