# FatSecret MCP Server

A Model Context Protocol (MCP) server for the FatSecret Platform API, giving an AI
agent food and recipe lookup, a food diary, an exercise log and weight history —
as four action-dispatch tools rather than twenty thin ones.

## Features

- 🔍 **Food Search**: Search foods and recipes, get nutrition facts, real GTIN/UPC barcode lookup
- 📖 **Food Diary**: Track meals, and aggregate a date range into one server-side report
- 🏃 **Exercise Tracking**: Log workouts and calories burned
- ⚖️ **Weight Management**: Track weight over time
- 📈 **Charting**: A credential-free `fatsecret-chart` script, JSON in, PNG out

## Quick Start

### 1. Installation

To run it, you do not need to install anything — see [Running it](#running-it)
below, which launches it straight from git with `uvx`. To work on it:

```bash
git clone https://github.com/hbs-1991/fitmeai.git
cd fitmeai

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -e ".[chart,dev]"
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

### 4. Authorize user-level access (one-time)

Food search works on the application credentials alone. The diary, exercise and
weight tools need a user access token, which comes from a three-legged OAuth 1.0
flow that opens a browser and listens on `localhost:8080`:

```bash
python setup_oauth.py
```

Record the resulting `FATSECRET_ACCESS_TOKEN` and `FATSECRET_ACCESS_SECRET`.
OAuth 1.0 tokens do not expire, so this happens once — and it must happen on a
machine with a browser, not on a headless server.

## Running it

```bash
uvx --from git+https://github.com/hbs-1991/fitmeai@<sha> fatsecret-mcp
```

with `FATSECRET_CONSUMER_KEY`, `FATSECRET_CONSUMER_SECRET`,
`FATSECRET_ACCESS_TOKEN` and `FATSECRET_ACCESS_SECRET` in the environment.

The platform page labels the app credentials **Consumer Key** and **Consumer
Secret** — that is the OAuth 1.0 naming. `FATSECRET_CLIENT_ID` and
`FATSECRET_CLIENT_SECRET` are accepted as aliases and win if both pairs are set,
so set one pair, not a mix. Pin a full 40-character commit
sha rather than a branch: a moving ref means the agent silently gets different
code one day.

The server speaks MCP over stdin/stdout and listens on no port. Any MCP client
can launch it; the shape above is what the `fatsecret` catalog entry in
[claude-hermes](https://github.com/hbs-1991/claude-hermes) uses.

## Available Tools

Four action-dispatch tools. `fatsecret_food` works on app credentials alone; the
other three appear only when a user access token is present.

| Tool | Actions |
|---|---|
| `fatsecret_food` | `search`, `get`, `barcode`, `create`, `recipe_search`, `recipe_get` |
| `fatsecret_diary` | `get`, `month`, `add`, `edit`, `delete`, `report` |
| `fatsecret_exercise` | `search`, `get`, `month`, `add`, `edit` |
| `fatsecret_weight` | `update`, `month` |

Four rather than twenty, each dispatching on a required `action` enum: every tool
schema lives in the calling model's cached prompt prefix and is paid for on every
request, whether or not the turn is about food. An action costs one enum value; a
tool costs a whole schema.

`fatsecret_diary(action="report", start=…, end=…)` aggregates a date range
server-side — daily rows, totals, averages and macro ratios — so a week of meals
reaches the model as one table rather than thirty rows of JSON.

Plus one console script, `fatsecret-chart`: JSON series on stdin, PNG out, no
credentials.

```bash
echo '[{"date":"2026-07-20","value":82.4},{"date":"2026-07-21","value":82.1}]' \
  | fatsecret-chart --out weight.png --title Weight --ylabel kg
```

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
├── __main__.py        # Console entry point: `fatsecret-mcp`
├── server.py          # FastMCP server setup
├── report.py          # Server-side period aggregation over the diary
├── config.py          # Configuration management
├── auth/              # OAuth authentication (keyring optional)
├── api/               # FatSecret API clients
├── tools/             # The four action-dispatch tools + dispatch.py
├── cli/               # fatsecret-chart — JSON in, PNG out, no credentials
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
