"""YouTube OAuth Helper: generate youtube_token.json from client_secrets.json."""
import argparse
import json
import pathlib
import sys
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
ROOT = pathlib.Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description="Authenticate with YouTube and save reusable token.")
    parser.add_argument(
        "--secrets", type=str, default=str(ROOT / "client_secrets.json"),
        help="Path to downloaded client_secrets.json from Google Cloud Console."
    )
    parser.add_argument(
        "--token", type=str, default=str(ROOT / "youtube_token.json"),
        help="Where to save the resulting OAuth token."
    )
    args = parser.parse_args()

    secrets_path = pathlib.Path(args.secrets)
    if not secrets_path.exists():
        sys.exit(
            f"Error: {secrets_path} not found!\n\n"
            "How to get client_secrets.json:\n"
            "1. Open: https://console.cloud.google.com/apis/credentials?project=gen-lang-client-0742279616\n"
            "2. Click '+ CREATE CREDENTIALS' -> 'OAuth client ID'\n"
            "3. Select Application type: 'Desktop app', name it 'yt-autopilot', and click Create\n"
            "4. Click 'DOWNLOAD JSON' and save it in this project folder as 'client_secrets.json'\n"
            "5. Run this script again: python src/auth_youtube.py\n"
        )

    print(f"Loading client secrets from: {secrets_path}")
    flow = InstalledAppFlow.from_client_secrets_file(str(secrets_path), SCOPES)
    print("Launching browser for one-click Google authentication...")
    creds = flow.run_local_server(port=0)

    token_path = pathlib.Path(args.token)
    token_dict = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes
    }
    token_path.write_text(json.dumps(token_dict, indent=2))
    print(f"\nAuthentication successful!")
    print(f"Token saved to: {token_path}")
    print("\nNext steps:")
    print("1. For local uploads: python src/run_phase3.py")
    print("2. For GitHub Actions: copy the entire contents of youtube_token.json into a GitHub secret named 'YOUTUBE_TOKEN'.")


if __name__ == "__main__":
    main()
