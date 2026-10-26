"""Phase 4a - Authenticate with TikTok Content Posting API and save reusable token."""
import argparse
import http.server
import json
import os
import pathlib
import sys
import urllib.parse
import requests

try:
    from dotenv import load_dotenv
    _env_path = pathlib.Path(__file__).resolve().parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(dotenv_path=_env_path)
except ImportError:
    pass

ROOT = pathlib.Path(__file__).resolve().parent.parent
REDIRECT_URI = "http://localhost:5000/callback"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"


class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    auth_code = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/callback":
            params = urllib.parse.parse_qs(parsed.query)
            if "code" in params:
                OAuthCallbackHandler.auth_code = params["code"][0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(
                    b"<html><body><h2>TikTok Authentication Successful!</h2>"
                    b"<p>You can close this tab now and return to your terminal.</p></body></html>"
                )
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Authorization failed: no code received.")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress default server logs


def main():
    parser = argparse.ArgumentParser(description="Authenticate with TikTok and generate tiktok_token.json.")
    parser.add_argument("--client-key", type=str, default=os.environ.get("TIKTOK_CLIENT_KEY"))
    parser.add_argument("--client-secret", type=str, default=os.environ.get("TIKTOK_CLIENT_SECRET"))
    parser.add_argument("--token-out", type=str, default=str(ROOT / "tiktok_token.json"))
    args = parser.parse_args()

    client_key = args.client_key
    client_secret = args.client_secret

    if not client_key or not client_secret:
        sys.exit(
            "Error: TIKTOK_CLIENT_KEY and TIKTOK_CLIENT_SECRET are required!\n"
            "Set them in your .env file or pass them via CLI:\n"
            "  TIKTOK_CLIENT_KEY=your_key\n"
            "  TIKTOK_CLIENT_SECRET=your_secret\n"
            "  python src/auth_tiktok.py\n"
        )

    state = "yt_autopilot_state"
    auth_url = (
        "https://www.tiktok.com/v2/auth/authorize/?"
        f"client_key={client_key}"
        "&scope=video.upload,video.publish"
        "&response_type=code"
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
        f"&state={state}"
    )

    print("\n=== TikTok Authentication ===")
    print("1. Visit this URL in your browser to authorize:")
    print(f"\n{auth_url}\n")
    print(f"2. Waiting for redirect callback on {REDIRECT_URI}...")

    server_address = ("localhost", 5000)
    httpd = http.server.HTTPServer(server_address, OAuthCallbackHandler)
    while OAuthCallbackHandler.auth_code is None:
        httpd.handle_request()

    code = OAuthCallbackHandler.auth_code
    print("Authorization code received! Exchanging for access token...")

    data = {
        "client_key": client_key,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post(TOKEN_URL, data=data, headers=headers, timeout=30)
    r.raise_for_status()
    resp_data = r.json()

    if "data" not in resp_data or "access_token" not in resp_data["data"]:
        sys.exit(f"Failed to obtain token from TikTok: {resp_data}")

    token_info = resp_data["data"]
    token_info["client_key"] = client_key
    token_info["client_secret"] = client_secret

    token_file = pathlib.Path(args.token_out)
    token_file.write_text(json.dumps(token_info, indent=2), encoding="utf-8")

    print(f"\nSuccess! TikTok token saved to {token_file}")
    print("To enable daily TikTok uploads in GitHub Actions:")
    print("Copy the contents of tiktok_token.json to a repository secret named TIKTOK_TOKEN.")


if __name__ == "__main__":
    main()
