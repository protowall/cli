"""ProtoWall API client — shared by CLI and MCP server."""

import os

import httpx


class ProtoWallClient:
    def __init__(self, api_key=None, api_url=None):
        self.api_key = api_key or os.environ.get("PROTOWALL_API_KEY", "")
        self.api_url = (api_url or os.environ.get("PROTOWALL_API_URL", "https://protowall.app")).rstrip("/")

        if not self.api_key:
            raise ValueError(
                "API key required. Set PROTOWALL_API_KEY or pass api_key.\n"
                "Create one at https://protowall.app/dashboard/"
            )

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _request(self, method, path, json_body=None, params=None, timeout=30):
        url = f"{self.api_url}/api/v1{path}"
        with httpx.Client(timeout=timeout) as http:
            resp = http.request(method, url, headers=self._headers(), json=json_body, params=params)
        data = resp.json()
        if resp.status_code >= 400:
            error = data.get("error", "Unknown error")
            code = data.get("code", "error")
            raise ApiError(error, code, resp.status_code, body=data)
        return data.get("data", data)

    def list_projects(self):
        return self._request("GET", "/projects")

    def create_project(self, name, destination_url, nda_text=None):
        body = {"name": name, "destination_url": destination_url}
        if nda_text:
            body["nda_text"] = nda_text
        return self._request("POST", "/projects", body)

    def get_project(self, slug):
        return self._request("GET", f"/projects/{slug}")

    def delete_project(self, slug):
        return self._request("DELETE", f"/projects/{slug}")

    def list_invites(self, slug):
        return self._request("GET", f"/projects/{slug}/invites")

    def send_invite(self, slug, email):
        return self._request("POST", f"/projects/{slug}/invites", {"email": email})

    def revoke_access(self, slug, invite_id):
        return self._request("POST", f"/projects/{slug}/invites/{invite_id}/revoke")

    def get_audit_log(self, slug, limit=50):
        return self._request("GET", f"/projects/{slug}/audit", params={"limit": limit})

    def rotate_secret(self, slug):
        return self._request("POST", f"/projects/{slug}/rotate-secret")

    def get_project_usage(self, slug, range_="7"):
        return self._request("GET", f"/projects/{slug}/usage", params={"range": range_})

    def get_invitee_engagement(self, slug, invite_id, range_="30"):
        return self._request(
            "GET", f"/projects/{slug}/invitees/{invite_id}/engagement",
            params={"range": range_},
        )

    def list_reviewer_sessions(self, slug, invite_id):
        """Read-only. Returns sessions with cached summaries; no API cost, no cap consumed."""
        return self._request(
            "GET", f"/projects/{slug}/invitees/{invite_id}/sessions",
        )

    def summarize_reviewer_session(self, slug, invite_id, session_start):
        """Generate (or fetch cached) summary for one session. Counts against the monthly cap."""
        return self._request(
            "POST", f"/projects/{slug}/invitees/{invite_id}/sessions/summarize",
            {"session_start": session_start},
            timeout=60,  # Sonnet round-trip can take 5-15s, leave generous headroom
        )

    def list_previews(self, slug, status=None):
        """List project previews. Pass status='open' to filter to only currently-resolving previews."""
        params = {"status": status} if status else None
        return self._request("GET", f"/projects/{slug}/previews", params=params)

    def create_preview(self, slug, slug_suffix, destination_url, label=None, external_ref=None):
        """Create a project preview (Pro). composite_slug is project.slug + '-' + slug_suffix."""
        body = {"slug_suffix": slug_suffix, "destination_url": destination_url}
        if label:
            body["label"] = label
        if external_ref:
            body["external_ref"] = external_ref
        return self._request("POST", f"/projects/{slug}/previews", body)

    def update_preview(self, slug, preview_id, destination_url=None, label=None, external_ref=None):
        """Update destination_url, label, or external_ref on a preview. The slug_suffix is immutable."""
        body = {}
        if destination_url is not None:
            body["destination_url"] = destination_url
        if label is not None:
            body["label"] = label
        if external_ref is not None:
            body["external_ref"] = external_ref
        return self._request("PATCH", f"/projects/{slug}/previews/{preview_id}", body)

    def close_preview(self, slug, preview_id):
        """Soft-close a preview. Idempotent. Closed previews stop resolving but keep their history."""
        return self._request("POST", f"/projects/{slug}/previews/{preview_id}/close")

    def list_access_requests(self, slug, status=None):
        """List access requests on a project. Pass status='PENDING' / 'APPROVED' / 'DECLINED' to filter."""
        params = {"status": status} if status else None
        return self._request("GET", f"/projects/{slug}/requests", params=params)

    def approve_access_request(self, slug, request_id):
        """Approve a pending access request — creates an Invite and sends the standard invite email."""
        return self._request("POST", f"/projects/{slug}/requests/{request_id}/approve")

    def decline_access_request(self, slug, request_id):
        """Decline a pending access request. Silent — no email back to the requester."""
        return self._request("POST", f"/projects/{slug}/requests/{request_id}/decline")


class ApiError(Exception):
    def __init__(self, message, code, status, body=None):
        self.message = message
        self.code = code
        self.status = status
        self.body = body or {}
        super().__init__(f"{message} ({code})")
