# ProtoWall

CLI and MCP server for managing ProtoWall projects, invites, and access.

## Install

```bash
pip install protowall
```

Or from source:
```bash
git clone https://github.com/protowall/mcp-server.git
cd mcp-server
pip install .
```

## API Key

Create an API key at [protowall.app/dashboard](https://protowall.app/dashboard/) and set it:

```bash
export PROTOWALL_API_KEY="pw_sk_your_key_here"
```

## CLI

```bash
protowall projects                          # List projects
protowall project <slug>                    # Get project detail
protowall project create <name> <url>       # Create project
protowall project delete <slug>             # Delete project
protowall invites <slug>                    # List invites
protowall invite <slug> <email>             # Send invite
protowall revoke <slug> <invite-id>         # Revoke access
protowall audit <slug>                      # View audit log
protowall rotate-secret <slug>              # Rotate origin secret
```

All commands output JSON for easy piping:
```bash
protowall projects | jq '.[0].slug'
```

## MCP Server

Add to your agent's MCP config:

**Claude Code** (`~/.claude/settings.json` or project `.claude/settings.json`):
```json
{
  "mcpServers": {
    "protowall": {
      "command": "protowall-mcp",
      "env": {
        "PROTOWALL_API_KEY": "pw_sk_your_key_here"
      }
    }
  }
}
```

**Cursor** (`.cursor/mcp.json` in your project root):
```json
{
  "mcpServers": {
    "protowall": {
      "command": "protowall-mcp",
      "env": {
        "PROTOWALL_API_KEY": "pw_sk_your_key_here"
      }
    }
  }
}
```

### Available Tools

| Tool | Description |
|---|---|
| `list_projects` | List all projects you own |
| `create_project` | Create a new project with an NDA wall |
| `send_invite` | Invite a reviewer by email |
| `revoke_access` | Revoke a reviewer's access immediately |
| `get_audit_log` | View audit events for a project |
| `rotate_secret` | Rotate the origin secret |

Once configured, ask your agent things like:

- "Create a ProtoWall project for my prototype at https://my-app.onrender.com"
- "Invite reviewer@example.com to my-project"
- "Show the audit log for my-project"

## Environment Variables

| Variable | Required | Default |
|---|---|---|
| `PROTOWALL_API_KEY` | Yes | — |
| `PROTOWALL_API_URL` | No | `https://protowall.app` |
