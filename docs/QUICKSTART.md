# FatSecret MCP Server - Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites

- Python 3.10+
- FatSecret API credentials ([Get them here](https://platform.fatsecret.com/api))
- Claude Desktop or another MCP client

## Installation (2 minutes)

```bash
# 1. Navigate to project directory
cd D:\projects\fatsecret_mcp

# 2. Install dependencies
pip install fastmcp requests pydantic python-dotenv keyring

# Done! ✅
```

## Configuration (1 minute)

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env with your credentials
notepad .env
```

Add your credentials:
```env
FATSECRET_CLIENT_ID=your_client_id_here
FATSECRET_CLIENT_SECRET=your_client_secret_here
```

Save and close.

## Choose Your Mode

### Option A: Public API (No Auth) 🔓

For food and recipe search only:

```bash
python main_noauth.py
```

**What works:**
- ✅ Search foods
- ✅ Get nutrition facts
- ✅ Search recipes
- ❌ Food diary
- ❌ Exercise tracking
- ❌ Weight tracking

### Option B: Full Features (With Auth) 🔐

For diary, exercise, and weight tracking:

**Step 1: Setup OAuth (one-time)**
```bash
python setup_oauth.py
```

This will:
1. Open your browser
2. Ask you to log in to FatSecret
3. Request permission
4. Store tokens securely

Takes ~30 seconds.

**Step 2: Start server**
```bash
python main.py
```

**What works:**
- ✅ Everything from Option A
- ✅ Food diary
- ✅ Exercise tracking
- ✅ Weight tracking

## Configure Claude Desktop (1 minute)

**Windows:**
```bash
# 1. Open config file
notepad %APPDATA%\Claude\claude_desktop_config.json
```

**Add this:**
```json
{
  "mcpServers": {
    "fatsecret": {
      "command": "python",
      "args": ["D:\\projects\\fatsecret_mcp\\main.py"]
    }
  }
}
```

**Change the path** to match your installation!

**Save and restart Claude Desktop.**

## Test It! (1 minute)

Open Claude Desktop and try:

```
Search for "banana" nutrition
```

You should see:
- Food name
- Calories
- Macros (protein, carbs, fat)
- Vitamins and minerals

If authenticated, also try:
```
Log 2 eggs for breakfast
Show my food diary for today
```

## Troubleshooting

### "FATSECRET_CLIENT_ID is not set"
→ Check your .env file exists and has credentials

### "No valid access token"
→ Run `python setup_oauth.py` to authorize

### Server not showing in Claude Desktop
→ Check the path in claude_desktop_config.json
→ Restart Claude Desktop completely

### Still stuck?
See [docs/setup.md](docs/setup.md) for detailed help.

## What's Next?

### Learn More
- [Setup Guide](docs/setup.md) - Detailed installation
- [Authentication](docs/authentication.md) - OAuth explained
- [Tools Reference](docs/tools_reference.md) - All 20 tools

### Try Examples
```bash
# Food search demo
python examples/search_foods.py

# Diary tracking demo (requires auth)
python examples/track_meal.py
```

### Common Tasks

**Track a meal:**
```
Log 2 scrambled eggs and toast for breakfast
```

**Track exercise:**
```
I went running for 30 minutes this morning
```

**Track weight:**
```
My weight today is 70.5 kg
```

**Find recipes:**
```
Find me a healthy chocolate cake recipe
```

**View history:**
```
Show my food diary for this week
What's my weight trend this month?
```

## Quick Reference

### 20 Tools Available

| Tool | What It Does |
|------|--------------|
| `fatsecret_food_search` | Search foods |
| `fatsecret_food_get` | Get nutrition facts |
| `fatsecret_recipe_search` | Search recipes |
| `fatsecret_recipe_get` | Get recipe details |
| `fatsecret_diary_add_entry` | Log food |
| `fatsecret_diary_get_entries` | View diary |
| `fatsecret_exercise_add_entry` | Log exercise |
| `fatsecret_weight_update` | Record weight |
| ... and 12 more! | See [Tools Reference](docs/tools_reference.md) |

### File Locations

| File | Purpose |
|------|---------|
| `main_noauth.py` | Public API server |
| `main.py` | Authenticated server |
| `setup_oauth.py` | OAuth setup |
| `.env` | Your credentials |
| `docs/` | Documentation |
| `examples/` | Code examples |

## Support

- 📖 **Full Documentation**: [docs/](docs/)
- 🐛 **Report Issues**: [GitHub Issues](https://github.com/yourusername/fatsecret-mcp/issues)
- 🌐 **FatSecret API**: https://platform.fatsecret.com/api

---

**Time to get started**: ~5 minutes
**Ready to use**: Immediately after setup ✅
