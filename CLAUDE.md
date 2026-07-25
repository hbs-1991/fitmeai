# FatSecret MCP Server

An MCP server for the FatSecret Platform API. It speaks MCP over stdin/stdout and
listens on no port; an MCP client launches it as a child process.

The nutrition-agent persona that used to live in this file — the Russian-language
dietitian, the memory files, the confirm-before-write rules — moved to
[claude-hermes](https://github.com/hbs-1991/claude-hermes), which owns the
persona, the user profile, memory and the skills. This repository is now only the
server and its one credential-free chart script.

## Layout

```
src/fatsecret_mcp/
├── __main__.py        # console entry point: `fatsecret-mcp`
├── server.py          # FastMCP server; registers the four tools
├── report.py          # server-side period aggregation over the diary
├── config.py          # configuration
├── auth/              # OAuth 1.0 (keyring is optional; env vars work alone)
├── api/               # FatSecret API clients
├── tools/             # the four action-dispatch tools + dispatch.py plumbing
├── cli/               # fatsecret-chart — JSON in, PNG out, no credentials
├── models/            # pydantic data models
└── utils/             # logging, errors
```

## Rules that are not obvious

- **Four tools, not twenty.** Every tool schema lives in the calling model's
  cached prompt prefix and is paid for on every request. Adding a fifth tool is a
  real cost; adding an action to an existing one is nearly free.
  `tests/test_prefix_budget.py` caps the four combined docstrings at 4,800
  characters. If you are over budget, move the prose into a skill in
  claude-hermes — do not raise the constant.
- **Tools return `{"error": "..."}`; they never raise.** An exception crossing
  the MCP boundary reads to the model as an infrastructure failure it cannot fix.
  The `guard` decorator in `tools/dispatch.py` enforces this; every tool is
  declared `-> dict` and must actually return one, because FastMCP rejects a
  non-dict payload as a protocol error that escapes `guard`.
- **Never log to stdout.** That is the pipe the MCP protocol runs on. `utils/logging.py`
  handles this; do not add a `print()` to server-side code.
- **`cli/chart.py` must stay credential-free.** No `api/`, no `config`, no
  `auth`, no `os.environ` — a test asserts it. It is reachable from an agent's
  shell, so it is given nothing worth reading.
- **`setup_oauth.py` needs a browser.** The three-legged OAuth 1.0 flow opens one
  and listens on `localhost:8080`, so it runs on a workstation, never on the VPS.
  The tokens it produces do not expire.

## Development

```bash
pip install -e ".[chart,dev]"
python -m pytest -q
ruff check src/ tests/
```
