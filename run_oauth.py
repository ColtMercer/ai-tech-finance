"""Run TikTok OAuth flow - opens auth URL and waits for callback."""
from src.poster.auth import run_oauth_flow, build_auth_url

SCOPES = ["video.publish", "user.info.basic"]

print("=== TikTok OAuth Flow ===")
auth_url = build_auth_url(state="auth_state", scopes=SCOPES)
print(f"\nOpen this URL in your browser:\n\n{auth_url}\n")
print("Waiting for callback on http://localhost:8080/callback ...")

token = run_oauth_flow(scopes=SCOPES)
print(f"\n✅ Token obtained!")
print(f"   Access token: {token.access_token[:20]}...")
print(f"   Expires at: {token.expires_at}")
print(f"   Scope: {token.scope}")
