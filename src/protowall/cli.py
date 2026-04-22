"""ProtoWall CLI — manage projects, invites, and access from the terminal."""

import json
import sys

from protowall.client import ProtoWallClient, ApiError


def _client():
    try:
        return ProtoWallClient()
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        raise SystemExit(1)


def _print(data):
    if isinstance(data, (dict, list)):
        print(json.dumps(data, indent=2))
    else:
        print(data)


def _error(e):
    print(f"Error: {e.message} ({e.code})", file=sys.stderr)
    raise SystemExit(1)


def cmd_projects(args):
    """List all projects."""
    try:
        _print(_client().list_projects())
    except ApiError as e:
        _error(e)


def cmd_project_get(args):
    """Get project detail."""
    if not args:
        print("Usage: protowall project <slug>", file=sys.stderr)
        raise SystemExit(1)
    try:
        _print(_client().get_project(args[0]))
    except ApiError as e:
        _error(e)


def cmd_project_create(args):
    """Create a new project."""
    if len(args) < 2:
        print("Usage: protowall project create <name> <destination_url> [nda_text]", file=sys.stderr)
        raise SystemExit(1)
    nda_text = args[2] if len(args) > 2 else None
    try:
        _print(_client().create_project(args[0], args[1], nda_text))
    except ApiError as e:
        _error(e)


def cmd_project_delete(args):
    """Delete a project."""
    if not args:
        print("Usage: protowall project delete <slug>", file=sys.stderr)
        raise SystemExit(1)
    try:
        _print(_client().delete_project(args[0]))
    except ApiError as e:
        _error(e)


def cmd_invites(args):
    """List invites for a project."""
    if not args:
        print("Usage: protowall invites <project-slug>", file=sys.stderr)
        raise SystemExit(1)
    try:
        _print(_client().list_invites(args[0]))
    except ApiError as e:
        _error(e)


def cmd_invite(args):
    """Send an invite."""
    if len(args) < 2:
        print("Usage: protowall invite <project-slug> <email>", file=sys.stderr)
        raise SystemExit(1)
    try:
        _print(_client().send_invite(args[0], args[1]))
    except ApiError as e:
        _error(e)


def cmd_revoke(args):
    """Revoke an invite."""
    if len(args) < 2:
        print("Usage: protowall revoke <project-slug> <invite-id>", file=sys.stderr)
        raise SystemExit(1)
    try:
        _print(_client().revoke_access(args[0], args[1]))
    except ApiError as e:
        _error(e)


def cmd_audit(args):
    """Get audit log for a project."""
    if not args:
        print("Usage: protowall audit <project-slug> [limit]", file=sys.stderr)
        raise SystemExit(1)
    limit = int(args[1]) if len(args) > 1 else 50
    try:
        _print(_client().get_audit_log(args[0], limit))
    except ApiError as e:
        _error(e)


def cmd_rotate_secret(args):
    """Rotate origin secret for a project."""
    if not args:
        print("Usage: protowall rotate-secret <project-slug>", file=sys.stderr)
        raise SystemExit(1)
    try:
        _print(_client().rotate_secret(args[0]))
    except ApiError as e:
        _error(e)


COMMANDS = {
    "projects": ("List all projects", cmd_projects),
    "project": ("Get project detail: project <slug>", cmd_project_get),
    "project create": ("Create project: project create <name> <url>", cmd_project_create),
    "project delete": ("Delete project: project delete <slug>", cmd_project_delete),
    "invites": ("List invites: invites <slug>", cmd_invites),
    "invite": ("Send invite: invite <slug> <email>", cmd_invite),
    "revoke": ("Revoke access: revoke <slug> <invite-id>", cmd_revoke),
    "audit": ("Audit log: audit <slug> [limit]", cmd_audit),
    "rotate-secret": ("Rotate secret: rotate-secret <slug>", cmd_rotate_secret),
}


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help", "help"):
        print("ProtoWall CLI\n")
        print("Usage: protowall <command> [args]\n")
        print("Commands:")
        for name, (desc, _) in COMMANDS.items():
            print(f"  {name:20s} {desc}")
        print(f"\nSet PROTOWALL_API_KEY to authenticate.")
        print("Create a key at https://protowall.app/dashboard/")
        raise SystemExit(0)

    # Check for two-word commands (e.g. "project create")
    two_word = f"{args[0]} {args[1]}" if len(args) > 1 else ""
    if two_word in COMMANDS:
        _, handler = COMMANDS[two_word]
        handler(args[2:])
    elif args[0] in COMMANDS:
        _, handler = COMMANDS[args[0]]
        handler(args[1:])
    else:
        print(f"Unknown command: {args[0]}", file=sys.stderr)
        print("Run 'protowall help' for usage.", file=sys.stderr)
        raise SystemExit(1)
