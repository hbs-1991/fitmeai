# FatSecret MCP Server - Setup Guide

This guide walks you through setting up the FatSecret MCP Server.

## Prerequisites

- Python 3.10 or higher
- FatSecret Platform API credentials
- Claude Desktop (or another MCP client)

## Step 1: Get FatSecret API Credentials

1. Go to https://platform.fatsecret.com/api
2. Click "Request an API Key" or sign in to your developer account
3. Create a new application:
   - Application Name: "My MCP Server" (or your choice)
   - Application Type: "Desktop Application"
4. Note your **Client ID** and **Client Secret**

## Step 2: Install the Server

### Option A: Install from source

```bash
# Clone the repository
git clone https://github.com/yourusername/fatsecret-mcp.git
cd fatsecret-mcp

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install fastmcp requests pydantic python-dotenv keyring
```

### Option B: Install from PyPI (when available)

```bash
pip install fatsecret-mcp
```

## Step 3: Configure Environment

1. Create a `.env` file in the project root:

```bash
cp .env.example .env
```

2. Edit `.env` and add your credentials:

```env
FATSECRET_CLIENT_ID=your_client_id_here
FATSECRET_CLIENT_SECRET=your_client_secret_here

# Optional: Customize other settings
LOG_LEVEL=INFO
```

## Step 4: Choose Your Mode

### Mode A: Public API Only (No Authentication)

For food and recipe search without user-specific features:

```bash
python main_noauth.py
```

**Available features:**
- ✅ Food search
- ✅ Recipe search
- ✅ Nutrition information
- ❌ Food diary
- ❌ Exercise tracking
- ❌ Weight management

### Mode B: Full Features (With Authentication)

For diary, exercise, and weight tracking:

1. Run the OAuth setup (one-time):

```bash
python setup_oauth.py
```

This will:
- Open your browser
- Ask you to log in to FatSecret
- Request permission to access your data
- Store tokens securely in Windows Credential Manager

2. Start the authenticated server:

```bash
python main.py
```

**Available features:**
- ✅ Food search
- ✅ Recipe search
- ✅ Nutrition information
- ✅ Food diary
- ✅ Exercise tracking
- ✅ Weight management

## Step 5: Configure Claude Desktop

Add the server to your Claude Desktop configuration:

**Location:**
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**Configuration:**

For public API mode:
```json
{
  "mcpServers": {
    "fatsecret": {
      "command": "python",
      "args": ["D:\\path\\to\\fatsecret_mcp\\main_noauth.py"]
    }
  }
}
```

For authenticated mode:
```json
{
  "mcpServers": {
    "fatsecret": {
      "command": "python",
      "args": ["D:\\path\\to\\fatsecret_mcp\\main.py"]
    }
  }
}
```

Replace `D:\\path\\to\\fatsecret_mcp` with your actual path.

## Step 6: Restart Claude Desktop

1. Close Claude Desktop completely
2. Reopen Claude Desktop
3. The FatSecret server should now be available

## Verify Installation

In Claude Desktop, try these commands:

**Test food search:**
```
Search for "apple" in FatSecret
```

**Test nutrition info:**
```
What's the nutrition information for a banana?
```

**Test diary (authenticated mode only):**
```
Log 2 eggs for breakfast today
```

## Troubleshooting

### Error: "FATSECRET_CLIENT_ID is not set"

- Make sure you created a `.env` file
- Check that your credentials are correct
- Ensure the `.env` file is in the project root directory

### Error: "Failed to authenticate with FatSecret API"

- Verify your Client ID and Client Secret are correct
- Check your internet connection
- Ensure you copied the credentials without extra spaces

### OAuth issues (authenticated mode)

- Try running `setup_oauth.py` again
- Check that your browser allows pop-ups
- Verify the callback URL is set to `http://localhost:8080/callback`

### Server not showing in Claude Desktop

- Check the path in `claude_desktop_config.json` is correct
- Ensure you used double backslashes (`\\`) in Windows paths
- Verify Python is in your system PATH
- Check Claude Desktop logs for error messages

## Next Steps

- Read [Authentication Guide](authentication.md) for OAuth details
- See [Tools Reference](tools_reference.md) for available tools
- Check out the [examples](../examples/) directory

## Support

- FatSecret API Docs: https://platform.fatsecret.com/api/Default.aspx
- Report issues: https://github.com/yourusername/fatsecret-mcp/issues
