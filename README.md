# FatSecret MCP Server

A comprehensive Model Context Protocol (MCP) server for the FatSecret Platform API, enabling AI agents to access nutrition tracking capabilities including food search, diary management, exercise tracking, and weight monitoring.

## Features

- 🔍 **Food Search**: Search foods, get nutrition facts, barcode scanning
- 📖 **Food Diary**: Track meals and daily nutrition
- 🏃 **Exercise Tracking**: Log workouts and calories burned
- ⚖️ **Weight Management**: Track weight over time
- 🍽️ **Saved Meals**: Create and manage meal templates
- 👤 **User Favorites**: Manage favorite foods and recipes

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/fatsecret-mcp.git
cd fatsecret-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

### 2. Get FatSecret API Credentials

1. Go to https://platform.fatsecret.com/api
2. Create a new application
3. Note your Client ID and Client Secret

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your credentials
# FATSECRET_CLIENT_ID=your_client_id
# FATSECRET_CLIENT_SECRET=your_client_secret
```

### 4. Run the Server

**Option A: Public API Only (No Authentication)**

For food and recipe search without user-specific features:

```bash
python main_noauth.py
```

**Option B: Full Features (With Authentication)**

For diary, exercise, and weight tracking:

```bash
# First, setup OAuth (one-time)
python setup_oauth.py

# Then start the server
python main.py
```

### 5. Configure Claude Desktop

Add to your Claude Desktop config (`%APPDATA%\Claude\claude_desktop_config.json` on Windows):

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

## Available Tools

### Food Search (Public - No Auth Required)
- `fatsecret_food_search` - Search foods by name
- `fatsecret_food_get` - Get detailed nutrition information
- `fatsecret_food_search_v3` - Advanced food search with filters
- `fatsecret_food_autocomplete` - Get autocomplete suggestions
- `fatsecret_food_barcode_scan` - Lookup food by barcode

### Food Diary (Authentication Required)
- `fatsecret_diary_get_entries` - Get all diary entries for date
- `fatsecret_diary_get_month` - Get monthly summary
- `fatsecret_diary_add_entry` - Add food to diary
- `fatsecret_diary_edit_entry` - Edit existing entry
- `fatsecret_diary_delete_entry` - Remove diary entry

### Exercise Tracking (Authentication Required)
- `fatsecret_exercise_search` - Search exercises
- `fatsecret_exercise_get_entries` - Get exercise entries for date
- `fatsecret_exercise_add_entry` - Log exercise
- `fatsecret_exercise_edit_entry` - Edit exercise entry

### Weight Management (Authentication Required)
- `fatsecret_weight_update` - Update weight for date
- `fatsecret_weight_get_month` - Get monthly weight history

## Usage Examples

### Search for Foods

```
User: "What's the nutrition info for a banana?"
```

### Track a Meal

```
User: "Log 2 scrambled eggs and toast for breakfast"
```

### Track Exercise

```
User: "Log 30 minutes of running this morning"
```

## Documentation

- [Setup Guide](docs/setup.md)
- [Authentication](docs/authentication.md)
- [Tools Reference](docs/tools_reference.md)

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Format code
black src/ tests/

# Lint code
ruff check src/ tests/
```

## Architecture

```
src/fatsecret_mcp/
├── server.py          # FastMCP server setup
├── config.py          # Configuration management
├── auth/              # OAuth authentication
├── api/               # FatSecret API clients
├── tools/             # MCP tool implementations
├── models/            # Pydantic data models
└── utils/             # Utilities (logging, errors)
```

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please open an issue or submit a pull request.

## Support

- FatSecret API Documentation: https://platform.fatsecret.com/api/Default.aspx
- Issues: https://github.com/yourusername/fatsecret-mcp/issues
