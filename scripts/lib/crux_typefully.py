"""Stdlib-only REST client for the Typefully API.

Manages draft creation, scheduling, listing, and deletion.
Auth via Bearer token stored in `.crux/bip/typefully.key`.
"""

from __future__ import annotations

import json
import os
from urllib.request import Request, urlopen


BASE_URL = "https://api.typefully.com/v2"


class TypefullyError(Exception):
    pass


class TypefullyClient:
    """Configured Typefully API client."""

    def __init__(self, bip_dir: str) -> None:
        config_path = os.path.join(bip_dir, "config.json")
        if not os.path.exists(config_path):
            raise TypefullyError(f"BIP config not found: {config_path}")

        with open(config_path) as f:
            config = json.load(f)

        self.social_set_id: int = config.get("social_set_id", 0)
        key_path = config.get("api_key_path", "")

        if not key_path or not os.path.exists(key_path):
            raise TypefullyError(f"API key file not found: {key_path}")

        with open(key_path) as f:
            self.api_key = f.read().strip()

    def _url(self, path: str) -> str:
        return f"{BASE_URL}/social-sets/{self.social_set_id}{path}"

    def _request(self, method: str, path: str, body: dict | None = None) -> dict | list:
        url = self._url(path)
        data = json.dumps(body).encode() if body else None
        req = Request(url, data=data, method=method)
        req.add_header("Authorization", f"Bearer {self.api_key}")
        req.add_header("Content-Type", "application/json")

        with urlopen(req) as resp:
            if resp.status >= 400:
                raise TypefullyError(f"Typefully API error: {resp.status}")
            return json.loads(resp.read().decode())


def create_draft(
    client: TypefullyClient,
    text: str,
    publish_at: str | None = None,
) -> dict:
    """Create a single-tweet draft."""
    body: dict = {
        "platforms": {
            "x": {
                "enabled": True,
                "posts": [{"text": text}],
            }
        }
    }
    if publish_at:
        body["publish_at"] = publish_at
    return client._request("POST", "/drafts", body)


def create_thread(
    client: TypefullyClient,
    posts: list[str],
    publish_at: str | None = None,
) -> dict:
    """Create a multi-tweet thread draft."""
    if not posts:
        raise TypefullyError("Cannot create thread with empty posts list")
    body: dict = {
        "platforms": {
            "x": {
                "enabled": True,
                "posts": [{"text": t} for t in posts],
            }
        }
    }
    if publish_at:
        body["publish_at"] = publish_at
    return client._request("POST", "/drafts", body)


def list_drafts(client: TypefullyClient) -> list:
    """List all drafts."""
    return client._request("GET", "/drafts")


def delete_draft(client: TypefullyClient, draft_id: int) -> dict:
    """Delete a draft by ID."""
    return client._request("DELETE", f"/drafts/{draft_id}")
