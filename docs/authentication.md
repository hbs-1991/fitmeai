# FatSecret MCP Server - Authentication Guide

This guide explains how authentication works in the FatSecret MCP Server.

## Overview

The server supports two authentication modes:

1. **Client Credentials** (Public API) - For food/recipe search
2. **Authorization Code** (User API) - For diary, exercise, weight tracking

## Authentication Modes

### 1. Client Credentials (Public API)

**Used for:**
- Food search
- Recipe search
- Nutrition information lookup
- Autocomplete suggestions

**Setup:**
Just add your API credentials to `.env`:

```env
FATSECRET_CLIENT_ID=your_client_id
FATSECRET_CLIENT_SECRET=your_client_secret
```

**How it works:**
- Server automatically requests access token from FatSecret
- Token cached and auto-refreshed when expired
- No user authorization required
- Cannot access user-specific data

**Start server:**
```bash
python main_noauth.py
```

---

### 2. Authorization Code (User API)

**Used for:**
- Food diary tracking
- Exercise logging
- Weight management
- Saved meals
- User favorites

**Setup:**
Run the OAuth setup wizard:

```bash
python setup_oauth.py
```

**How it works:**

1. **Authorization (One-time)**
   ```
   setup_oauth.py
   ↓
   Opens browser → FatSecret login page
   ↓
   User logs in and authorizes app
   ↓
   Redirects to localhost:8080/callback
   ↓
   Exchanges auth code for tokens
   ↓
   Stores tokens in Windows Credential Manager
   ```

2. **Runtime (Every server start)**
   ```
   main.py starts
   ↓
   Loads tokens from Windows Credential Manager
   ↓
   Checks if token expired (< 5 min remaining)
   ↓
   If expired: Automatically refreshes using refresh_token
   ↓
   Uses access_token for all API calls
   ```

**Token Storage:**

Tokens are stored securely in **Windows Credential Manager**:

- **Service Name**: `fatsecret_mcp`
- **Stored Keys**:
  - `access_token` - API access token (expires in ~1 hour)
  - `refresh_token` - Token to get new access tokens (long-lived)
  - `token_expiry` - ISO timestamp of token expiration

**View/Delete Tokens:**

Via Windows:
1. Search for "Credential Manager" in Start Menu
2. Click "Windows Credentials"
3. Look for entries starting with `fatsecret_mcp`

Via Python:
```python
from src.fatsecret_mcp.auth import OAuthManager

oauth = OAuthManager()

# Get tokens
access_token, refresh_token, expiry = oauth.get_stored_tokens()
print(f"Access Token: {access_token[:20]}...")
print(f"Expires: {expiry}")

# Clear tokens
oauth.clear_tokens()
```

**Start server:**
```bash
python main.py
```

## OAuth Flow Details

### Authorization Request

When you run `setup_oauth.py`, it generates this URL:

```
https://www.fatsecret.com/oauth/authorize?
  response_type=code&
  client_id=YOUR_CLIENT_ID&
  redirect_uri=http://localhost:8080/callback&
  scope=basic&
  state=RANDOM_STATE
```

**Parameters:**
- `response_type=code` - Request authorization code
- `client_id` - Your application ID
- `redirect_uri` - Where to send user after authorization
- `scope=basic` - Request basic access to user data
- `state` - Random token for CSRF protection

### Token Exchange

After user authorizes, FatSecret redirects to:

```
http://localhost:8080/callback?code=AUTH_CODE&state=RANDOM_STATE
```

The server then exchanges the code for tokens:

```bash
POST https://www.fatsecret.com/oauth/token
Authorization: Basic BASE64(client_id:client_secret)
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
code=AUTH_CODE&
redirect_uri=http://localhost:8080/callback
```

**Response:**
```json
{
  "access_token": "eyJhbG...",
  "refresh_token": "def502...",
  "expires_in": 3600,
  "token_type": "Bearer"
}
```

### Token Refresh

When access token expires (or < 5 min remaining), auto-refresh:

```bash
POST https://www.fatsecret.com/oauth/token
Authorization: Basic BASE64(client_id:client_secret)
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token&
refresh_token=REFRESH_TOKEN
```

**Response:**
```json
{
  "access_token": "eyJhbG...",
  "refresh_token": "def502...",
  "expires_in": 3600,
  "token_type": "Bearer"
}
```

## Security Best Practices

### 1. Protect Client Credentials

**DO:**
- Store in `.env` file (never commit)
- Use environment variables in production
- Rotate credentials if exposed

**DON'T:**
- Hard-code in source files
- Commit to version control
- Share with unauthorized users

### 2. Token Storage

**DO:**
- Use Windows Credential Manager (keyring)
- Encrypt at rest
- Clear tokens when done

**DON'T:**
- Store in plain text files
- Log access tokens
- Hard-code tokens

### 3. CSRF Protection

The OAuth flow uses `state` parameter for CSRF protection:

```python
# Generate random state
state = secrets.token_urlsafe(32)

# Include in authorization URL
auth_url = f"{base_url}?...&state={state}"

# Verify on callback
if callback_state != state:
    raise SecurityError("Invalid state")
```

### 4. Callback URL

The callback URL must be:
- `http://localhost:8080/callback` (as configured)
- Exact match in FatSecret API settings
- Not accessible from internet (localhost only)

## Troubleshooting

### Error: "No valid access token"

**Cause:** Tokens not found or expired
**Solution:**
```bash
python setup_oauth.py
```

### Error: "Failed to refresh token"

**Cause:** Refresh token expired or invalid
**Solution:**
```bash
# Clear old tokens and re-authorize
python -c "from src.fatsecret_mcp.auth import OAuthManager; OAuthManager().clear_tokens()"
python setup_oauth.py
```

### Error: "Invalid redirect_uri"

**Cause:** Callback URL mismatch
**Solution:**
1. Check `.env` file: `FATSECRET_OAUTH_CALLBACK_URL=http://localhost:8080/callback`
2. Verify FatSecret API settings match exactly
3. Ensure no trailing slash

### Error: "Authorization timeout"

**Cause:** User didn't complete authorization in 5 minutes
**Solution:**
- Run `setup_oauth.py` again
- Complete authorization promptly
- Check firewall allows localhost:8080

### Browser doesn't open

**Cause:** No default browser or blocked
**Solution:**
- Manually copy URL from terminal
- Paste in browser
- Complete authorization

## API Reference

### OAuthManager

```python
from src.fatsecret_mcp.auth import OAuthManager

oauth = OAuthManager()

# Get valid access token (auto-refresh if needed)
token = oauth.get_valid_access_token()

# Store tokens
oauth.store_tokens(access_token, refresh_token, expires_in)

# Get stored tokens
access_token, refresh_token, expiry = oauth.get_stored_tokens()

# Clear tokens
oauth.clear_tokens()

# Check if token expired
is_expired = oauth.is_token_expired(expiry_str)

# Refresh token
new_access, new_refresh, expires_in = oauth.refresh_access_token(refresh_token)
```

### Run OAuth Flow

```python
from src.fatsecret_mcp.auth import run_oauth_flow

# Interactive OAuth authorization
success = run_oauth_flow()
```

## Token Lifecycle

```
[Setup Phase - One Time]
user runs setup_oauth.py
→ browser opens
→ user logs in
→ user authorizes
→ tokens stored in keyring
→ done ✅

[Runtime Phase - Every Server Start]
main.py starts
→ load tokens from keyring
→ check expiry
→ if expired: refresh automatically
→ use valid access_token ✅

[Maintenance - As Needed]
if refresh fails
→ clear tokens
→ run setup_oauth.py again ✅
```

## Additional Resources

- [FatSecret OAuth Documentation](https://platform.fatsecret.com/api/Default.aspx?screen=rapiauth2)
- [OAuth 2.0 RFC 6749](https://tools.ietf.org/html/rfc6749)
- [Python keyring Documentation](https://keyring.readthedocs.io/)
