"""ProtoWall MCP Server — manage projects, invites, and access from coding agents."""

import json

from mcp.server.fastmcp import FastMCP

from protowall.client import ProtoWallClient, ApiError

mcp = FastMCP("ProtoWall", instructions=(
    "ProtoWall is a review platform for confidential prototypes. Builders invite reviewers, "
    "see what they engaged with, and capture signed feedback. An optional NDA gate can be "
    "turned on per project. Use these tools to manage projects, invites, previews, access "
    "requests, audit logs, and reviewer engagement."
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


@mcp.tool()
def list_reviewer_sessions(project_slug: str, invite_id: str) -> str:
    """List a reviewer's sessions with their cached AI summaries. **Read-only — no API cost, doesn't count against any cap.**

    A "session" is a contiguous run of access events with no gap longer than 30 minutes.
    Each session in the response includes a `summary` object (with headline + body_md) if
    one has already been generated, or `summary: null` if not. Top-level `summaries_used`
    and `summaries_cap` show the builder's current monthly usage.

    Use this first to discover what sessions exist and check remaining cap before calling
    `summarize_reviewer_session`.

    Args:
        project_slug: The project's slug
        invite_id: The invite ID for the reviewer (from list_invites)
    """
    return _call(_get_client().list_reviewer_sessions, project_slug, invite_id)


@mcp.tool()
def summarize_reviewer_session(project_slug: str, invite_id: str, session_start: str) -> str:
    """Generate (or fetch cached) AI summary for one specific reviewer session. **Counts against the builder's monthly summary cap (default 50/month, shared across dashboard, CLI, and agents).**

    Returns the cached summary if it already exists for that session_start — that case
    does NOT count against the cap. Use `list_reviewer_sessions` first if you want to
    check remaining cap or pick a specific session.

    **Design note:** Force-regenerating an active summary or clearing one are intentionally
    dashboard-only operations — there is no API/CLI/MCP equivalent. This keeps the monthly
    cap a meaningful boundary instead of an automation footgun. If you (the agent) want a
    custom narrative beyond the cached summary, pull raw events with `list_reviewer_sessions`
    or `get_reviewer_engagement` and compose your own story with your own model.

    Args:
        project_slug: The project's slug
        invite_id: The invite ID (from list_invites)
        session_start: ISO timestamp matching a session_start from list_reviewer_sessions
    """
    return _call(_get_client().summarize_reviewer_session, project_slug, invite_id, session_start)


@mcp.tool()
def list_previews(project_slug: str, only_open: bool = False) -> str:
    """List parallel previews of a project — per-PR / per-branch / per-experiment URLs.

    Each preview lives at `{project-slug}-{slug_suffix}.proxy.protowall.app` with its own
    destination URL. Reviewers' invites are project-level, so a single accepted invite
    covers every open preview automatically. Closed previews stop resolving but stay
    queryable for audit / engagement / feedback history.

    Args:
        project_slug: The project's slug
        only_open: If true, returns only currently-resolving previews. Default false (returns all).
    """
    return _call(_get_client().list_previews, project_slug, status="open" if only_open else None)


@mcp.tool()
def create_preview(
    project_slug: str,
    slug_suffix: str,
    destination_url: str,
    label: str = "",
    external_ref: str = "",
) -> str:
    """Create a parallel preview of a project. Pro plan only.

    The preview lives at `{project_slug}-{slug_suffix}.proxy.protowall.app`. Use this to
    spin up a separate URL for a PR, branch, or experiment without affecting the main
    project URL or its versions. `external_ref` is a free-form string for upstream
    reconciliation (e.g. "github:org/repo#42").

    Args:
        project_slug: The project's slug
        slug_suffix: The preview's slug suffix (e.g. "pr-42", "experiment-redesign")
        destination_url: Where this preview points (e.g. "https://acme-pr-42.preview.app")
        label: Optional human-readable label (e.g. "PR #42: redesign sidebar")
        external_ref: Optional upstream reference for reconciliation (e.g. "github:acme/web#42")
    """
    return _call(
        _get_client().create_preview,
        project_slug,
        slug_suffix,
        destination_url,
        label=label or None,
        external_ref=external_ref or None,
    )


@mcp.tool()
def update_preview(
    project_slug: str,
    preview_id: str,
    destination_url: str = "",
    label: str = "",
    external_ref: str = "",
) -> str:
    """Update destination_url, label, or external_ref on a preview. Pass empty strings to skip a field.

    The slug_suffix is immutable — to rename, close this preview and create a new one.
    Pass at least one of destination_url / label / external_ref.

    Args:
        project_slug: The project's slug
        preview_id: The preview ID (from list_previews)
        destination_url: New destination URL, or empty to leave unchanged
        label: New label, or empty to leave unchanged
        external_ref: New external_ref, or empty to leave unchanged
    """
    return _call(
        _get_client().update_preview,
        project_slug,
        preview_id,
        destination_url=destination_url or None,
        label=label or None,
        external_ref=external_ref or None,
    )


@mcp.tool()
def close_preview(project_slug: str, preview_id: str) -> str:
    """Soft-close a preview. Idempotent — closing an already-closed preview returns the current state.

    Closed previews stop resolving (their subdomain returns 404) but their audit / engagement
    / feedback history stays queryable. Use this when a PR merges or an experiment ends.

    Args:
        project_slug: The project's slug
        preview_id: The preview ID (from list_previews)
    """
    return _call(_get_client().close_preview, project_slug, preview_id)


@mcp.tool()
def list_access_requests(project_slug: str, status: str = "") -> str:
    """List access requests on a project. Strangers who land on the project URL can request access here.

    Pass `status="PENDING"` to see only requests awaiting your decision. `APPROVED` and `DECLINED`
    show historical decisions. Default (empty string) returns all.

    Args:
        project_slug: The project's slug
        status: Optional filter — "PENDING", "APPROVED", or "DECLINED". Empty for all.
    """
    return _call(_get_client().list_access_requests, project_slug, status=status or None)


@mcp.tool()
def approve_access_request(project_slug: str, request_id: str) -> str:
    """Approve a pending access request — creates an Invite and sends the standard invite email.

    Hits the same per-project invite cap as send_invite. On Free, the 5-invite cap surfaces
    an `invite_cap` error — decline the request, revoke an existing invitee, or upgrade.

    Args:
        project_slug: The project's slug
        request_id: The request ID (from list_access_requests)
    """
    return _call(_get_client().approve_access_request, project_slug, request_id)


@mcp.tool()
def decline_access_request(project_slug: str, request_id: str) -> str:
    """Decline a pending access request. Silent — no email back to the requester (privacy: don't leak project status).

    Args:
        project_slug: The project's slug
        request_id: The request ID (from list_access_requests)
    """
    return _call(_get_client().decline_access_request, project_slug, request_id)


def main():
    import asyncio
    asyncio.run(mcp.run_stdio_async())
