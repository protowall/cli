# ProtoWall

CLI and MCP server for managing ProtoWall projects, invites, and access.

## Install

```bash
pip install protowall
```

Or from source:
```bash
git clone https://github.com/protowall/cli.git
cd cli
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
protowall usage <slug> [7d|30d]             # Project usage analytics (Pro)
protowall reviewer <slug> <invite-id> [7d|30d]   # Per-reviewer engagement (Pro)
protowall sessions <slug> <invite-id>       # List sessions + cached AI summaries (Pro, read-only)
protowall summarize-session <slug> <invite-id> <session-start>   # Generate session summary (Pro, uses cap)
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
| `get_project_usage` | Project-wide engagement rollup over 7 or 30 days (Pro) |
| `get_reviewer_engagement` | Per-reviewer engagement rollup with top paths and timeline (Pro) |
| `list_reviewer_sessions` | List a reviewer's sessions with cached AI summaries (Pro, read-only — no cap consumed) |
| `summarize_reviewer_session` | Generate or fetch a cached AI summary for one session (Pro, counts against monthly cap) |

Once configured, ask your agent things like:

- "Create a ProtoWall project for my prototype at https://my-app.onrender.com"
- "Invite reviewer@example.com to my-project"
- "Show the audit log for my-project"
- "Who looked at my-project this week and what did they spend time on?"
- "Pull the engagement breakdown for the reviewer with invite id cvw80…"
- "Summarize what acme@corp.com did during their most recent session on my-project"

## Design notes

### Session summaries are dashboard-write, API-read

`summarize_reviewer_session` is **idempotent** — it returns a cached summary if one exists, otherwise it generates a fresh one (which counts against the builder's monthly cap of 50). It does NOT force-regenerate an active summary, and there is no `clear` or `regenerate` command on the CLI / MCP / API.

Those two operations are deliberately dashboard-only. The reasoning:

1. **The monthly cap stays a meaningful boundary.** Without a clear endpoint, no agent automation can quietly cycle summaries to "find the best framing" and burn through a builder's slots.
2. **Cleaner product split.** The cached AI summary is a UX convenience for dashboard users. Agents that want a custom narrative have raw events and durations available via `list_reviewer_sessions` and `get_reviewer_engagement` — bring your own model and your own budget.

If `list_reviewer_sessions` returns a session with `summary: null`, that can mean either "never generated" OR "generated then cleared." Either way, the right next step from an agent's perspective is the same: call `summarize_reviewer_session` to get an active one (or compose your own narrative from the raw events).

## Environment Variables

| Variable | Required | Default |
|---|---|---|
| `PROTOWALL_API_KEY` | Yes | — |
| `PROTOWALL_API_URL` | No | `https://protowall.app` |
