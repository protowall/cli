"""ProtoWall MCP Server — manage projects, invites, and access from coding agents."""

import os
import json

import httpx
from mcp.server.fastmcp import FastMCP

API_URL = os.environ.get("PROTOWALL_API_URL", "https://protowall.app").rstrip("/")
API_KEY = os.environ.get("PROTOWALL_API_KEY", "")

mcp = FastMCP("ProtoWall", instructions=(
    "ProtoWall puts an authentication and NDA wall in front of prototypes. "
    "Use these tools to manage projects, invite reviewers, revoke access, and view audit logs."
))


def _headers():
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


def _api(method, path, json_body=None):
    """Call the ProtoWall API and return the parsed response."""
    url = f"{API_URL}/api/v1{path}"
    with httpx.Client(timeout=30) as client:
        resp = client.request(method, url, headers=_headers(), json=json_body)
    data = resp.json()
    if resp.status_code >= 400:
        error = data.get("error", "Unknown error")
        code = data.get("code", "error")
        return f"Error ({code}): {error}"
    return json.dumps(data.get("data", data), indent=2)


@mcp.tool()
def list_projects() -> str:
    """List all projects you own. Returns project names, slugs, destination URLs, and origin secrets."""
    return _api("GET", "/projects")


@mcp.tool()
def create_project(name: str, destination_url: str, nda_text: str = "") -> str:
    """Create a new project with an NDA wall in front of your prototype.

    Args:
        name: Project name (e.g. "Acme Analytics")
        destination_url: URL of your prototype (e.g. "https://my-app.onrender.com")
        nda_text: Custom NDA text (Pro only). Leave empty for the default template.
    """
    body = {"name": name, "destination_url": destination_url}
    if nda_text:
        body["nda_text"] = nda_text
    return _api("POST", "/projects", body)


@mcp.tool()
def send_invite(project_slug: str, email: str) -> str:
    """Invite a reviewer to access a prototype. They'll receive an email with a link to accept the NDA.

    Args:
        project_slug: The project's slug (from list_projects)
        email: Reviewer's email address
    """
    return _api("POST", f"/projects/{project_slug}/invites", {"email": email})


@mcp.tool()
def revoke_access(project_slug: str, invite_id: str) -> str:
    """Revoke a reviewer's access. Their session is terminated immediately.

    Args:
        project_slug: The project's slug
        invite_id: The invite ID to revoke (from list_invites or send_invite response)
    """
    return _api("POST", f"/projects/{project_slug}/invites/{invite_id}/revoke")


@mcp.tool()
def get_audit_log(project_slug: str, limit: int = 20) -> str:
    """Get the audit log for a project. Shows invite sends, NDA acceptances, revocations, and access attempts.

    Args:
        project_slug: The project's slug
        limit: Number of events to return (max 100, default 20)
    """
    return _api("GET", f"/projects/{project_slug}/audit?limit={limit}")


@mcp.tool()
def rotate_secret(project_slug: str) -> str:
    """Rotate the origin secret for a project. Use this after revoking access or if the secret was exposed.

    Args:
        project_slug: The project's slug
    """
    return _api("POST", f"/projects/{project_slug}/rotate-secret")


if __name__ == "__main__":
    if not API_KEY:
        print("Error: PROTOWALL_API_KEY environment variable is required.")
        print("Create an API key at https://protowall.app/dashboard/")
        raise SystemExit(1)
    mcp.run()
