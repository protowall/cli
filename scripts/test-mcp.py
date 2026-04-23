"""ProtoWall MCP server smoke test.

Validates that all MCP tools are registered and the API client works correctly.
Full MCP protocol testing happens when the server is used in Claude Code/Cursor.

Usage: PROTOWALL_API_KEY=pw_sk_... python scripts/test-mcp.py
"""

import json
import os
import sys

PASS = 0
FAIL = 0


def check(label, expected, actual):
    global PASS, FAIL
    if expected == actual:
        print(f"  ✓ {label}")
        PASS += 1
    else:
        print(f"  ✗ {label} (expected {expected!r}, got {actual!r})")
        FAIL += 1


def main():
    global PASS, FAIL

    api_key = os.environ.get("PROTOWALL_API_KEY")
    if not api_key:
        print("Error: PROTOWALL_API_KEY is required")
        sys.exit(1)

    print("\nProtoWall MCP server smoke test\n")

    # --- Tool registration ---
    print("Tool registration")
    from protowall.mcp_server import mcp
    tools = mcp._tool_manager.list_tools()
    tool_names = [t.name for t in tools]
    check("Has 6 tools", 6, len(tools))
    for name in ["list_projects", "create_project", "send_invite", "revoke_access", "get_audit_log", "rotate_secret"]:
        check(f"Has {name}", True, name in tool_names)

    # --- API client ---
    print("\nAPI client")
    from protowall.client import ProtoWallClient, ApiError
    client = ProtoWallClient(api_key=api_key)
    check("Client created", True, client is not None)

    # List projects
    projects = client.list_projects()
    check("list_projects returns list", True, isinstance(projects, list))

    # Create project
    project = client.create_project("MCP Smoke Test", "https://example.com")
    check("create_project returns dict", True, isinstance(project, dict))
    slug = project.get("slug")
    check("Project has slug", True, slug is not None)
    print(f"  (slug: {slug})")

    # Get project detail
    detail = client.get_project(slug)
    check("get_project returns detail", True, "invite_count" in detail)

    # Send invite
    invite = client.send_invite(slug, "mcp-smoke@protowall.app")
    check("send_invite returns invite", True, "id" in invite)
    invite_id = invite["id"]
    check("Invite status is PENDING", "PENDING", invite.get("status"))

    # List invites
    invites = client.list_invites(slug)
    check("list_invites returns list", True, isinstance(invites, list))
    check("Has 1 invite", 1, len(invites))

    # Audit log
    audit = client.get_audit_log(slug)
    check("get_audit_log has events", True, audit.get("total", 0) >= 1)

    # Revoke
    revoked = client.revoke_access(slug, invite_id)
    check("Revoke status is REVOKED", "REVOKED", revoked.get("status"))

    # Double revoke should fail
    try:
        client.revoke_access(slug, invite_id)
        check("Double revoke raises error", True, False)
    except ApiError as e:
        check("Double revoke raises error", "already_revoked", e.code)

    # Rotate secret
    result = client.rotate_secret(slug)
    secret = result.get("origin_secret", "")
    check("Rotate returns pw_proj_ secret", True, secret.startswith("pw_proj_"))

    # Cleanup
    print("\nCleanup")
    client.delete_project(slug)
    try:
        client.get_project(slug)
        check("Project deleted", True, False)
    except ApiError:
        check("Project deleted", True, True)

    print(f"\nResults: {PASS} passed, {FAIL} failed")
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
