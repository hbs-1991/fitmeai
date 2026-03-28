"""Export OAuth tokens from keyring to .env format.

Run locally after setup_oauth.py to get tokens for Docker:
    python export_tokens.py >> .env
"""

import keyring

token = keyring.get_password("fatsecret_mcp", "oauth1_access_token")
secret = keyring.get_password("fatsecret_mcp", "oauth1_access_secret")

if token and secret:
    print(f"FATSECRET_ACCESS_TOKEN={token}")
    print(f"FATSECRET_ACCESS_SECRET={secret}")
else:
    print("# No tokens found. Run setup_oauth.py first.", flush=True)
    raise SystemExit(1)
