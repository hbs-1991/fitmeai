# Nutrition Agent — Design Specification

**Date:** 2026-03-28
**Status:** Draft
**Author:** User + Claude

---

## 1. Overview

Personal nutrition and fitness AI agent accessible via Telegram bot. The agent uses Claude Agent SDK with FatSecret MCP tools to automate food diary management, meal planning, exercise tracking, and weekly nutrition analysis.

**Key characteristics:**
- Single user (personal use)
- Telegram as primary interface
- Claude Agent SDK (Approach 1 — Claude Code under the hood)
- Existing FatSecret MCP server reused as-is
- Subscription OAuth authentication (no separate API key cost)

---

## 2. Architecture

```
Telegram User (single user)
    |
    | text / voice / photo / barcode
    v
+-----------------------------------------------+
|  Telegram Bot (aiogram 3.26)                   |
|                                                |
|  handlers/                                     |
|    text.py     — plain text messages           |
|    voice.py    — OGG -> Whisper API -> text    |
|    photo.py    — image -> pyzbar or base64     |
|    commands.py — /start /profile /report /plan |
|                                                |
|  services/                                     |
|    whisper.py        — OpenAI Whisper client   |
|    barcode.py        — pyzbar decoding         |
|    session_manager.py — chat_id <-> session_id |
+----------------------+------------------------+
                       |
                       v
+-----------------------------------------------+
|  Claude Agent SDK (query / resume)             |
|                                                |
|  system_prompt:                                |
|    preset: "claude_code"                       |
|    append: nutrition agent instructions        |
|                                                |
|  setting_sources: ["project"]                  |
|    -> loads CLAUDE.md, skills, hooks           |
|                                                |
|  permission_mode: "bypassPermissions"          |
|                                                |
|  mcp_servers:                                  |
|    fatsecret: python main.py (stdio)           |
|                                                |
|  allowed_tools:                                |
|    - Read, Write (for images + memory)         |
|    - Skill (for analysis/planning skills)      |
|    - mcp__fatsecret__* (all FatSecret tools)   |
|                                                |
|  max_turns: 20                                 |
|  max_budget_usd: 1.0                           |
+----------------------+------------------------+
                       |
                       v
+-----------------------------------------------+
|  FatSecret MCP Server (existing, unchanged)    |
|                                                |
|  Public tools (no auth):                       |
|    food_search, food_get, food_autocomplete    |
|    food_search_v3, food_barcode_scan           |
|    recipe_search, recipe_get                   |
|                                                |
|  Authenticated tools (OAuth):                  |
|    diary_get_entries, diary_get_month           |
|    diary_add_entry, diary_edit_entry            |
|    diary_delete_entry                           |
|    exercise_search, exercise_get_entries        |
|    exercise_get_month, exercise_add_entry       |
|    exercise_edit_entry, exercise_delete_entry   |
|    weight_update, weight_get_month              |
+-----------------------------------------------+
```

---

## 3. Authentication

### Anthropic (Claude Agent SDK)

Uses subscription OAuth instead of API key. Two options:

1. **`claude auth login`** — one-time browser login, credentials stored in `~/.claude/.credentials.json`. Agent SDK inherits automatically.
2. **`claude setup-token`** — generates long-lived OAuth token, stored as `ANTHROPIC_AUTH_TOKEN` in `.env`. Better for headless/daemon operation.

Authentication precedence (Agent SDK inherits from Claude Code CLI):
1. Cloud provider credentials (Bedrock/Vertex/Foundry)
2. `ANTHROPIC_AUTH_TOKEN` environment variable
3. `ANTHROPIC_API_KEY` environment variable
4. `apiKeyHelper` script
5. Subscription OAuth from `claude auth login`

**Decision:** Use `ANTHROPIC_AUTH_TOKEN` from `claude setup-token` in `.env` for reliability in daemon mode. Fallback: `claude auth login` session.

### OpenAI (Whisper only)

`OPENAI_API_KEY` in `.env`. Used exclusively for voice message transcription.

### FatSecret

Existing OAuth 2.0 flow. Tokens stored in Windows Credential Manager (keyring). Single-user — one set of credentials.

### Telegram

`TELEGRAM_BOT_TOKEN` from @BotFather in `.env`.

---

## 4. Message Handling

### Incoming Messages

| Type | Processing | Agent Input |
|------|-----------|-------------|
| **Text** | Direct passthrough | `query(prompt=text)` |
| **Voice** | Download OGG -> OpenAI Whisper API -> text | `query(prompt="[Voice]: {transcription}")` |
| **Photo (barcode)** | Download -> pyzbar decode -> barcode number | `query(prompt="Find food by barcode {number}")` |
| **Photo (food)** | Download -> base64 encode | Streaming input with image content block |
| **Photo (unknown)** | Try pyzbar first; if no barcode -> treat as food photo | Fallback to image analysis |

### Barcode Detection Logic

```python
from pyzbar import pyzbar
from PIL import Image

image = Image.open(photo_path)
barcodes = pyzbar.decode(image)

if barcodes:
    barcode_number = barcodes[0].data.decode()
    # Text prompt with barcode number
    prompt = f"Find food by barcode {barcode_number} and show nutrition info"
else:
    # No barcode -> food photo -> streaming input with base64
    prompt = streaming_input_with_image(photo_path, "Identify this food...")
```

### Image Handling (Streaming Input Mode)

Agent SDK requires streaming input for images (single message mode does not support image attachments):

```python
async def streaming_input_with_image(image_path: str, text: str):
    import base64
    with open(image_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode()

    async def message_stream():
        yield {
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    {"type": "text", "text": text},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_b64,
                        },
                    },
                ],
            },
        }

    return message_stream()
```

### Outgoing Messages (Streaming via sendMessageDraft)

Telegram Bot API 9.3+ supports `sendMessageDraft` for streaming partial responses:

```python
draft_id = unique_draft_id()
accumulated_text = ""

async for message in query(prompt=..., options=options):
    if isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, TextBlock):
                accumulated_text += block.text
                await bot.send_message_draft(
                    chat_id=chat_id,
                    draft_id=draft_id,
                    text=accumulated_text[:4096],
                )

# Final message replaces draft
await bot.send_message(chat_id=chat_id, text=accumulated_text)
```

### Threaded Mode (Topics)

Enable via @BotFather -> Threaded Mode for parallel conversations:

- **Main chat** — general queries, quick questions
- **Topic: Diary** — food logging
- **Topic: Meal Plan** — weekly plans
- **Topic: Workouts** — exercise planning
- **Topic: Analysis** — weekly reports

Each topic maps to its own Agent SDK session via `message_thread_id -> session_id`.

---

## 5. Session Management

### Session Persistence

Map `chat_id` (+ optional `message_thread_id`) to Agent SDK `session_id`:

```python
# session_manager.py
class SessionManager:
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self.sessions: dict[str, str] = {}  # key -> session_id
        self._load()

    def _key(self, chat_id: int, thread_id: int | None = None) -> str:
        return f"{chat_id}:{thread_id or 0}"

    def get_session(self, chat_id: int, thread_id: int | None = None) -> str | None:
        return self.sessions.get(self._key(chat_id, thread_id))

    def set_session(self, chat_id: int, session_id: str, thread_id: int | None = None):
        self.sessions[self._key(chat_id, thread_id)] = session_id
        self._save()
```

### Session Resume

```python
session_id = session_manager.get_session(chat_id, thread_id)

if session_id:
    # Resume existing conversation
    options = ClaudeAgentOptions(resume=session_id)
else:
    # New session
    options = base_options()

async for message in query(prompt=user_text, options=options):
    if hasattr(message, "subtype") and message.subtype == "init":
        session_manager.set_session(chat_id, message.session_id, thread_id)
    ...
```

---

## 6. Memory System

### Why Custom Memory (not Auto Memory)

Auto Memory (`~/.claude/projects/<project>/memory/`) is a **CLI-only feature** and is **never loaded by the SDK**. We implement equivalent functionality using hooks + Write tool.

### Architecture

```
memory/
  MEMORY.md              # Index file, loaded via hook at session start
  eating_patterns.md     # Eating habits, frequent meals, timing
  favorite_foods.md      # Frequently logged foods with portions
  corrections.md         # User corrections ("not thigh, breast")
  weekly_insights.md     # Conclusions from weekly analysis
```

### Memory Loading (Hook)

```python
async def load_memory(input_data, tool_use_id, context):
    """Inject memory content at session start."""
    memory_dir = Path(PROJECT_DIR) / "memory"
    content_parts = []

    memory_index = memory_dir / "MEMORY.md"
    if memory_index.exists():
        content_parts.append(memory_index.read_text(encoding="utf-8"))

    for f in sorted(memory_dir.glob("*.md")):
        if f.name != "MEMORY.md":
            content_parts.append(f"## {f.stem}\n{f.read_text(encoding='utf-8')}")

    return {"additionalContext": "\n\n".join(content_parts)} if content_parts else {}

# Applied in options:
hooks = {
    "UserPromptSubmit": [
        HookMatcher(matcher=".*", hooks=[load_memory])
    ]
}
```

### Memory Writing

The agent updates memory files via Write tool. Instructions in CLAUDE.md:

```markdown
## Memory Rules
After each interaction, if you learned something new about the user's habits:
- New frequent food -> append to memory/favorite_foods.md
- Correction -> append to memory/corrections.md
- New eating pattern -> append to memory/eating_patterns.md
- Analysis insight -> append to memory/weekly_insights.md
- Always update memory/MEMORY.md index accordingly
```

### User Profile (`about_me.md`)

Static file maintained by the user. Referenced in CLAUDE.md via `@about_me.md` import:

```markdown
# User Profile

## Physical Parameters
- Gender: male
- Age: XX years
- Height: XXX cm
- Current weight: XX kg
- Target weight: XX kg

## Goals
- Primary goal: weight loss / muscle gain / maintenance
- Target calories: XXXX kcal/day
- Macros target: protein XXXg / fat XXg / carbs XXXg

## Lifestyle
- Activity level: sedentary / moderate / active
- Workouts: X times/week, type
- Work schedule: XX:XX - XX:XX
- Sleep: XX:XX - XX:XX

## Food Preferences
- Allergies/intolerances: ...
- Don't eat: ...
- Prefer: ...
- Cuisine: ...

## Meal Schedule
- Breakfast: ~XX:XX
- Lunch: ~XX:XX
- Dinner: ~XX:XX
- Snacks: yes/no
```

---

## 7. Skills

Skills are Markdown files in `.claude/skills/*/SKILL.md`. Loaded on demand via `setting_sources: ["project"]` + `allowed_tools: ["Skill"]`.

### Analytical Skills

#### nutrition-analysis
**Trigger:** "analyze nutrition", "weekly analysis", "analyze my diet"
**Algorithm:**
1. Get diary entries via `fatsecret_diary_get_month` / `fatsecret_diary_get_entries`
2. Calculate averages: calories, protein, fat, carbs
3. Compare with targets from `about_me.md`
4. Identify patterns: missed meals, macro imbalances
5. Output: daily breakdown table, average vs target, problem areas, recommendations

#### weight-dynamics
**Trigger:** "weight dynamics", "weight progress", "weight trend"
**Algorithm:**
1. Get weight history via `fatsecret_weight_get_month`
2. Calculate trend (gaining/losing/stagnating)
3. Project timeline to target weight
4. Suggest calorie adjustments if needed

#### workout-analysis
**Trigger:** "workout analysis", "exercise summary"
**Algorithm:**
1. Get exercise history via `fatsecret_exercise_get_month`
2. Analyze frequency, volume, calories burned
3. Recommend adjustments based on goals

### Planning Skills

#### meal-planner
**Trigger:** "meal plan", "what to eat this week"
**Algorithm:**
1. Read current analysis + goals from about_me.md
2. Generate 7-day meal plan with specific dishes from FatSecret
3. Calculate total KBJU per day
4. Respect food preferences and allergies

#### daily-menu
**Trigger:** "what to eat today", "today's menu"
**Algorithm:**
1. Check what's already eaten today via diary
2. Calculate remaining KBJU budget
3. Suggest remaining meals to hit targets

#### workout-planner
**Trigger:** "workout plan", "what to do in the gym"
**Algorithm:**
1. Review goals + exercise history
2. Suggest training session for today/week

### Utility Skills

#### quick-log
**Trigger:** "log", "I ate...", food photo
**Algorithm:**
1. Identify food (from text, photo, or barcode)
2. Search in FatSecret
3. Confirm with user (portion, meal type)
4. Add to diary via `fatsecret_diary_add_entry`

#### weekly-report
**Trigger:** "weekly report", scheduled on Sundays
**Algorithm:**
1. Combine: nutrition analysis + weight dynamics + workout analysis
2. Generate comprehensive report
3. Provide recommendations for next week
4. Update memory/weekly_insights.md

---

## 8. CLAUDE.md (Agent Instructions)

```markdown
# Nutrition Agent

You are a personal nutritionist and fitness trainer. You help the user
track their nutrition, plan meals, analyze eating patterns, suggest
workouts, and maintain a healthy lifestyle.

## User Profile
Read @about_me.md for all user parameters, goals, and preferences.
Always consider these when making recommendations.

## Memory
Your memory files are in the memory/ directory. They are loaded
automatically via hook at session start. When you learn something new:
- New frequent food -> Write to memory/favorite_foods.md
- User correction -> Write to memory/corrections.md
- New pattern discovered -> Write to memory/eating_patterns.md
- Analysis insight -> Write to memory/weekly_insights.md
- Update memory/MEMORY.md index after changes

## Communication Style
- Respond in Russian (user's language)
- Be concise but informative
- Use tables for nutrition data
- Always show KBJU (calories, protein, fat, carbs)
- Warn if daily intake deviates >20% from target

## Available Tools
- FatSecret MCP tools for food/diary/exercise/weight operations
- Read tool for viewing food photos
- Write tool for updating memory files
- Skills for analysis and planning

## Workflow Rules
- When user sends a food photo: identify food, estimate portion,
  search in FatSecret, confirm before adding to diary
- When user sends a barcode photo: look up by barcode number
- When user asks for analysis: use appropriate analysis skill
- When user asks for a plan: use planning skill
- Always confirm before adding/editing/deleting diary entries
```

---

## 9. Project Structure

```
D:/projects/fatsecret_mcp/
|
|-- src/fatsecret_mcp/              # Existing MCP server (unchanged)
|   |-- api/                        # FatSecret API clients
|   |-- tools/                      # MCP tool implementations
|   |-- models/                     # Pydantic models
|   |-- auth/                       # OAuth
|   |-- server.py                   # FastMCP server
|   +-- config.py
|
|-- main.py                         # MCP server entry (existing)
|
|-- nutrition_agent/                # NEW: Telegram bot + Agent SDK
|   |-- __init__.py
|   |-- bot.py                      # aiogram dispatcher + router
|   |-- agent.py                    # Agent SDK wrapper (query/resume/hooks)
|   |-- handlers/
|   |   |-- __init__.py
|   |   |-- text.py                 # Text message handler
|   |   |-- voice.py                # Voice -> Whisper -> text
|   |   |-- photo.py                # Photo -> barcode/image
|   |   +-- commands.py             # /start /profile /report /plan
|   |-- services/
|   |   |-- __init__.py
|   |   |-- whisper.py              # OpenAI Whisper API client
|   |   |-- barcode.py              # pyzbar decoding
|   |   +-- session_manager.py      # chat_id <-> session_id mapping
|   +-- config.py                   # Bot configuration
|
|-- about_me.md                     # User profile (static, user-maintained)
|-- memory/                         # Dynamic agent memory
|   |-- MEMORY.md                   # Index
|   |-- eating_patterns.md
|   |-- favorite_foods.md
|   |-- corrections.md
|   +-- weekly_insights.md
|
|-- CLAUDE.md                       # Agent system instructions
|-- .claude/
|   +-- skills/                     # Agent skills
|       |-- nutrition-analysis/SKILL.md
|       |-- weight-dynamics/SKILL.md
|       |-- workout-analysis/SKILL.md
|       |-- meal-planner/SKILL.md
|       |-- daily-menu/SKILL.md
|       |-- workout-planner/SKILL.md
|       |-- quick-log/SKILL.md
|       +-- weekly-report/SKILL.md
|
|-- .env                            # Credentials (gitignored)
|-- .env.example                    # Template
|-- pyproject.toml                  # Updated with new dependencies
+-- run_bot.py                      # Entry point: python run_bot.py
```

---

## 10. Dependencies

### New (added to pyproject.toml)

```toml
"claude-agent-sdk>=0.1.51"   # Claude Agent SDK
"aiogram>=3.26.0"            # Telegram bot framework
"openai>=1.0.0"              # Whisper API for voice transcription
"pyzbar>=0.1.9"              # Barcode decoding from images
"Pillow>=10.0.0"             # Image processing
```

### System Dependencies

- `libzbar0` (Linux) or `zbar` (Windows/macOS) — required by pyzbar
- Python 3.10+
- Claude Code CLI (bundled with claude-agent-sdk)

### Existing (unchanged)

```toml
"fastmcp>=3.0.0"
"requests"
"pydantic"
"python-dotenv"
"keyring"
```

---

## 11. Environment Variables

```env
# Anthropic (choose ONE):
# Option A: OAuth token from subscription (preferred, free)
ANTHROPIC_AUTH_TOKEN=your-token-from-claude-setup-token
# Option B: API key (paid per token)
# ANTHROPIC_API_KEY=sk-ant-...

# Telegram Bot
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...

# OpenAI (Whisper voice transcription only)
OPENAI_API_KEY=sk-...

# FatSecret (existing)
FATSECRET_CLIENT_ID=...
FATSECRET_CLIENT_SECRET=...
```

---

## 12. Cost Analysis

| Component | Auth Method | Cost |
|-----------|------------|------|
| Claude Agent SDK | Subscription OAuth | $0 (included in Max $100/mo) |
| OpenAI Whisper | API key | ~$0.006/min of audio |
| FatSecret API | Client credentials | Free tier (5000 calls/day) |
| Telegram Bot API | Bot token | Free |
| **Total marginal cost** | | **~$0.01-0.05/day** (voice only) |

---

## 13. Limitations and Risks

| Risk | Mitigation |
|------|-----------|
| Agent SDK session startup latency (3-7s) | Acceptable for Telegram bot; user sees "typing..." indicator |
| Subscription rate limits | Personal use, unlikely to hit limits |
| FatSecret API rate limits | 5000 calls/day, sufficient for personal use |
| Memory files growing large | Periodic cleanup; agent instructed to keep concise |
| pyzbar barcode detection accuracy | Fallback to image analysis if no barcode detected |
| Whisper transcription errors | Agent can ask for clarification; corrections saved to memory |
| MCP server process management | Agent SDK manages stdio lifecycle automatically |

---

## 14. Future Enhancements

- Scheduled weekly reports (cron or Telegram scheduled messages)
- Integration with fitness trackers (Garmin, Apple Health) via additional MCP tools
- Photo-based portion estimation improvements
- Recipe suggestions based on available ingredients
- Shopping list generation from meal plans
