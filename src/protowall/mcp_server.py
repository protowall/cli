"""ProtoWall MCP Server — manage projects, invites, and access from coding agents."""

import json

from mcp.server.fastmcp import FastMCP

from protowall.client import ProtoWallClient, ApiError

mcp = FastMCP("ProtoWall", instructions=(
    "ProtoWall puts an authentication and NDA wall in front of prototypes. "
    "Use these tools to manage projects, invite reviewers, revoke access, and view audit logs."
))

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = ProtoWallClient()
    return _client


def _call(fn, *args, **kwargs):
    try:
        result = fn(*args, **kwargs)
        return json.dumps(result, indent=2)
    except ApiError as e:
        return f"Error ({e.code}): {e.message}"


@mcp.tool()
def list_projects() -> str:
    """List all projects you own. Returns project names, slugs, destination URLs, and origin secrets."""
    return _call(_get_client().list_projects)


@mcp.tool()
def create_project(name: str, destination_url: str, nda_text: str = "") -> str:
    """Create a new project with an NDA wall in front of your prototype.

    Args:
        name: Project name (e.g. "Acme Analytics")
        destination_url: URL of your prototype (e.g. "https://my-app.onrender.com")
        nda_text: Custom NDA text (Pro only). Leave empty for the default template.
    """
    return _call(_get_client().create_project, name, destination_url, nda_text or None)


@mcp.tool()
def send_invite(project_slug: str, email: str) -> str:
    """Invite a reviewer to access a prototype. They'll receive an email with a link to accept the NDA.

    Args:
        project_slug: The project's slug (from list_projects)
        email: Reviewer's email address
    """
    return _call(_get_client().send_invite, project_slug, email)


@mcp.tool()
def revoke_access(project_slug: str, invite_id: str) -> str:
    """Revoke a reviewer's access. Their session is terminated immediately.

    Args:
        project_slug: The project's slug
        invite_id: The invite ID to revoke (from list_invites or send_invite response)
    """
    return _call(_get_client().revoke_access, project_slug, invite_id)


@mcp.tool()
def get_audit_log(project_slug: str, limit: int = 20) -> str:
    """Get the audit log for a project. Shows invite sends, NDA acceptances, revocations, and access attempts.

    Args:
        project_slug: The project's slug
        limit: Number of events to return (max 100, default 20)
    """
    return _call(_get_client().get_audit_log, project_slug, limit)


@mcp.tool()
def rotate_secret(project_slug: str) -> str:
    """Rotate the origin secret for a project. Use this after revoking access or if the secret was exposed.

    Args:
        project_slug: The project's slug
    """
    return _call(_get_client().rotate_secret, project_slug)


@mcp.tool()
def get_project_usage(project_slug: str, range: str = "7") -> str:
    """Get project usage analytics — unique reviewers, total views, top routes, daily timeline. Pro plan only.

    Reviewer engagement only: static assets and the builder's own preview traffic
    are filtered out. Use this to answer "who looked at my prototype this week
    and what did they actually do?".

    Args:
        project_slug: The project's slug
        range: Window length. Accepts "7", "30", "7d", or "30d". Defaults to 7.
    """
    return _call(_get_client().get_project_usage, project_slug, range)


@mcp.tool()
def get_reviewer_engagement(project_slug: str, invite_id: str, range: str = "30") -> str:
    """Get per-reviewer engagement — total views, first/last seen, top paths, daily timeline. Pro plan only.

    Use this to dig into one specific reviewer's behaviour: "what did acme@corp.com
    actually look at on the Q2 prototype, and how long did they spend?".

    Args:
        project_slug: The project's slug
        invite_id: The invite ID for the reviewer (from list_invites)
        range: Window length. Accepts "7", "30", "7d", or "30d". Defaults to 30.
    """
    return _call(_get_client().get_invitee_engagement, project_slug, invite_id, range)


def main():
    import asyncio
    asyncio.run(mcp.run_stdio_async())
