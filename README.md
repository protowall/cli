# ProtoWall MCP Server

MCP server for managing ProtoWall projects, invites, and access from coding agents like Claude Code and Cursor.

## Setup

1. Clone this repo:
```bash
git clone https://github.com/protowall/mcp-server.git
cd mcp-server
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create an API key at [protowall.app/dashboard](https://protowall.app/dashboard/) — click "Create key" in the API Keys section.

4. Add to your Claude Code config (`~/.claude/settings.json`):
```json
{
  "mcpServers": {
    "protowall": {
      "command": "python",
      "args": ["/path/to/mcp-server/server.py"],
      "env": {
        "PROTOWALL_API_KEY": "pw_sk_your_key_here"
      }
    }
  }
}
```

## Available Tools

| Tool | Description |
|---|---|
| `list_projects` | List all projects you own |
| `create_project` | Create a new project with an NDA wall |
| `send_invite` | Invite a reviewer by email |
| `revoke_access` | Revoke a reviewer's access immediately |
| `get_audit_log` | View audit events for a project |
| `rotate_secret` | Rotate the origin secret |

## Usage

Once configured, you can ask your coding agent things like:

- "Create a ProtoWall project for my prototype at https://my-app.onrender.com"
- "Invite reviewer@example.com to my-project"
- "Show the audit log for my-project"
- "Revoke access for invite xyz"

## Environment Variables

| Variable | Required | Default |
|---|---|---|
| `PROTOWALL_API_KEY` | Yes | — |
| `PROTOWALL_API_URL` | No | `https://protowall.app` |
