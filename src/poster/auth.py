from __future__ import annotations

import base64
import hashlib
import http.server
import json
import os
import socketserver
import threading
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import httpx

from src.config import get_config, get_logger, get_mongo_client, DB_NAME, COLLECTION_POSTS

AUTH_BASE_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"


@dataclass
class OAuthToken:
    access_token: str
    refresh_token: str
    expires_at: datetime
    scope: str


class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    code: Optional[str] = None
    state: Optional[str] = None

    def do_GET(self) -> None:  # noqa: N802
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        OAuthCallbackHandler.code = params.get("code", [None])[0]
        OAuthCallbackHandler.state = params.get("state", [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"Authorization received. You can close this window.")

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


def _generate_pkce() -> tuple[str, str]:
    """Generate PKCE code_verifier and code_challenge."""
    code_verifier = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b"=").decode("ascii")
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return code_verifier, code_challenge

# Module-level storage for PKCE verifier (needed across auth URL generation and token exchange)
_pkce_verifier: str = ""

def build_auth_url(state: str, scopes: list[str]) -> str:
    global _pkce_verifier
    config = get_config()
    _pkce_verifier, code_challenge = _generate_pkce()
    params = {
        "client_key": config.tiktok_client_key,
        "redirect_uri": config.tiktok_redirect_uri,
        "scope": ",".join(scopes),
        "state": state,
        "response_type": "code",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return f"{AUTH_BASE_URL}?{urllib.parse.urlencode(params)}"


def exchange_code_for_token(code: str) -> OAuthToken:
    config = get_config()
    logger = get_logger()

    data = {
        "client_key": config.tiktok_client_key,
        "client_secret": config.tiktok_client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": config.tiktok_redirect_uri,
        "code_verifier": _pkce_verifier,
    }

    response = httpx.post(TOKEN_URL, data=data, timeout=30)
    response.raise_for_status()
    payload = response.json()

    if "data" not in payload:
        raise RuntimeError(f"TikTok token error: {payload}")

    token_data = payload["data"]
    expires_at = datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 0))

    token = OAuthToken(
        access_token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token", ""),
        expires_at=expires_at,
        scope=token_data.get("scope", ""),
    )

    logger.info("TikTok access token obtained; expires at %s", expires_at)
    return token


def refresh_access_token(refresh_token: str) -> OAuthToken:
    config = get_config()

    data = {
        "client_key": config.tiktok_client_key,
        "client_secret": config.tiktok_client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    response = httpx.post(TOKEN_URL, data=data, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if "data" not in payload:
        raise RuntimeError(f"TikTok refresh error: {payload}")

    token_data = payload["data"]
    expires_at = datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 0))
    return OAuthToken(
        access_token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token", refresh_token),
        expires_at=expires_at,
        scope=token_data.get("scope", ""),
    )


def store_token(token: OAuthToken) -> None:
    client = get_mongo_client()
    collection = client[DB_NAME][COLLECTION_POSTS]
    collection.update_one(
        {"type": "oauth_token"},
        {
            "$set": {
                "type": "oauth_token",
                "access_token": token.access_token,
                "refresh_token": token.refresh_token,
                "expires_at": token.expires_at,
                "scope": token.scope,
                "updated_at": datetime.utcnow(),
            }
        },
        upsert=True,
    )


def load_token() -> Optional[OAuthToken]:
    client = get_mongo_client()
    doc = client[DB_NAME][COLLECTION_POSTS].find_one({"type": "oauth_token"})
    if not doc:
        return None
    return OAuthToken(
        access_token=doc["access_token"],
        refresh_token=doc.get("refresh_token", ""),
        expires_at=doc["expires_at"],
        scope=doc.get("scope", ""),
    )


def ensure_token(scopes: list[str]) -> OAuthToken:
    logger = get_logger()
    token = load_token()
    if token and token.expires_at > datetime.utcnow() + timedelta(minutes=5):
        return token

    if token and token.refresh_token:
        logger.info("Refreshing TikTok access token")
        token = refresh_access_token(token.refresh_token)
        store_token(token)
        return token

    logger.info("No valid TikTok token found. Initiate OAuth flow.")
    raise RuntimeError("TikTok OAuth required. Use run_oauth_flow() to authorize.")


def run_oauth_flow(scopes: list[str], port: int = 8080, state: str = "state") -> OAuthToken:
    logger = get_logger()
    auth_url = build_auth_url(state=state, scopes=scopes)
    logger.info("Open this URL to authorize: %s", auth_url)

    with socketserver.TCPServer(("", port), OAuthCallbackHandler) as httpd:
        thread = threading.Thread(target=httpd.handle_request)
        thread.start()
        thread.join(timeout=300)

    if not OAuthCallbackHandler.code:
        raise RuntimeError("OAuth callback not received.")

    token = exchange_code_for_token(OAuthCallbackHandler.code)
    store_token(token)
    return token
