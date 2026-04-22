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

    def _request(self, method, path, json_body=None, params=None):
        url = f"{self.api_url}/api/v1{path}"
        with httpx.Client(timeout=30) as http:
            resp = http.request(method, url, headers=self._headers(), json=json_body, params=params)
        data = resp.json()
        if resp.status_code >= 400:
            error = data.get("error", "Unknown error")
            code = data.get("code", "error")
            raise ApiError(error, code, resp.status_code)
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


class ApiError(Exception):
    def __init__(self, message, code, status):
        self.message = message
        self.code = code
        self.status = status
        super().__init__(f"{message} ({code})")
