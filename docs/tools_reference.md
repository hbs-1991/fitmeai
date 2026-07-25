# FatSecret MCP Server — Tools Reference

## Overview

Four tools, each dispatching on a required `action` enum. Not twenty thin ones:
every tool schema lives in the calling model's cached prompt prefix and is paid
for on every request, whether or not the turn is about food. An action costs one
enum value; a tool costs a whole schema.

Every tool returns a plain dict, always. On failure it returns
`{"error": "..."}` rather than raising — an exception crossing the MCP boundary
reads to a model as an infrastructure failure it cannot fix, while an error
string reads as something to correct and retry. A missing parameter names *every*
missing field at once, not the first one, so a model does not spend four round
trips discovering four required fields.

`fatsecret_food` registers on the application credentials alone.
`fatsecret_diary`, `fatsecret_exercise` and `fatsecret_weight` register only when
`FATSECRET_ACCESS_TOKEN` and `FATSECRET_ACCESS_SECRET` are present.

---

## `fatsecret_food`

Look up foods and recipes in the FatSecret database.

| Action | Requires | Optional |
|---|---|---|
| `search` | `query` | `max_results` (20), `page` (0) |
| `get` | `food_id` | — |
| `barcode` | `barcode` | — |
| `create` | `query`, `nutrition` | — |
| `recipe_search` | `query` | `max_results` (20), `page` (0) |
| `recipe_get` | `recipe_id` | — |

**`get` is not optional before logging.** The serving list it returns is the only
place `serving_id` comes from, and a `serving_id` remembered from another food
belongs to that other food — it produces plausible, wrong numbers.

**`barcode`** calls FatSecret's real `food.find_id_for_barcode` endpoint and then
fetches the food. Digits are zero-padded to GTIN-13, so a 12-digit UPC-A or an
8-digit EAN-8 works as given; without the padding the lookup silently misses a
product that is actually in the database. A miss returns a clean error, not an
exception — unbranded and homemade food has no barcode, and the caller should
fall back to `search` or `create`.

**`create`** takes `nutrition` as an object with `serving_size`, `calories`,
`fat`, `carbohydrate` and `protein`. Optionally inside the same object:
`brand_name` (defaults to `"Homemade"`), `brand_type` (`manufacturer`,
`restaurant` or `supermarket`, defaulting to `manufacturer`), and any further
nutrients the API accepts. Returns `{"food_id": "..."}`.

```python
fatsecret_food(action="search", query="chicken breast")
fatsecret_food(action="get", food_id="1641")
fatsecret_food(action="barcode", barcode="012000161155")
fatsecret_food(action="create", query="Омлет с сыром",
               nutrition={"serving_size": "1 порция", "calories": 320,
                          "fat": 24, "carbohydrate": 3, "protein": 22})
```

---

## `fatsecret_diary`

Read, write and summarize the user's food diary.

| Action | Requires | Optional |
|---|---|---|
| `get` | — | `entry_date` (today) |
| `month` | — | `year`, `month` (current) |
| `add` | `food_id`, `food_entry_name`, `serving_id`, `meal` | `number_of_units` (1.0), `entry_date` |
| `edit` | `food_entry_id` | `serving_id`, `number_of_units`, `meal` |
| `delete` | `food_entry_id` | — |
| `report` | `start`, `end` | `target_calories` |

`meal` is one of `breakfast`, `lunch`, `dinner`, `other`. There is no `snack`.

### `number_of_units` — the one thing that goes wrong

Read the serving description returned by `fatsecret_food(action="get", …)`:

- **A gram-based serving** (`"100 g"`) means the unit *is one gram*.
  200 g → `number_of_units=200`. **Not** `200/100 = 2`.
- **Any other serving** (`"1 cup"`, `"1 breast"`) means `number_of_units` counts
  those servings. Two cups → `2`. Half a breast → `0.5`.

Dividing grams by the serving size is the single most common logging error.

### `report`

Aggregates `[start, end]` server-side and returns daily rows plus period totals,
averages and macro ratios — because a week of raw diary JSON is the most
expensive thing this server could put in a model's context, and summing thirty
verbose rows token-by-token is arithmetic no model should be doing.

Dates are `YYYY-MM-DD`; the range is capped at 92 days; one API call is made per
*month*, never per day. Passing `target_calories` adds an `off_target_days` list
naming every day deviating by more than 20%.

**Averages divide by days logged, not days in the range.** An unlogged day is
missing data, not a zero-calorie day, and averaging it in invents a deficit that
is really just a day the user forgot to log.

```python
fatsecret_diary(action="add", food_id="1641", food_entry_name="Куриная грудка",
                serving_id="50321", meal="lunch", number_of_units=200)
fatsecret_diary(action="report", start="2026-07-20", end="2026-07-26",
                target_calories=2000)
```

---

## `fatsecret_exercise`

Look up exercises and manage the activity log.

| Action | Requires | Optional |
|---|---|---|
| `search` | `query` | `max_results` (20) |
| `get` | — | `entry_date` (today) |
| `month` | — | `year`, `month` (current) |
| `add` | `exercise_id`, `minutes` | `entry_date` |
| `edit` | `exercise_entry_id`, `minutes` | — |

FatSecret's day is **fully allocated**: adding an exercise reduces the minutes
credited to the default resting activity. A logged workout does not simply add
calories on top of the day.

---

## `fatsecret_weight`

Record and read the user's weight history.

| Action | Requires | Optional |
|---|---|---|
| `update` | `weight_kg` | `entry_date` (today), `comment` |
| `month` | — | `year`, `month` (current) |

---

## `fatsecret-chart` (console script, not an MCP tool)

Renders a dated series to a PNG. Reads JSON on stdin, prints the output path.

```bash
echo '[{"date":"2026-07-20","value":82.4},{"date":"2026-07-21","value":82.1}]' \
  | fatsecret-chart --out weight.png --title Weight --ylabel kg
```

It knows nothing about FatSecret: no API client, no config, no environment, no
network. It is reachable from an agent's shell, and everything reachable from a
shell is assumed readable by the agent — so it is given nothing worth reading.
Requires the `chart` extra (`pip install ".[chart]"`).

---

## Common workflows

**Log a meal.** `food(action="search")` → `food(action="get")` to read the
serving list → confirm the resulting calories and macros with the user →
`diary(action="add")` → `diary(action="get")` to verify it landed under the
intended meal with the calories that were quoted. The `add` call returning a
`food_entry_id` is not verification.

**Report on a week.** `diary(action="report", start=…, end=…, target_calories=…)`
returns finished arithmetic. Format it; do not recompute it.

**Chart the weight trend.** `weight(action="month")` → reshape to
`[{"date": …, "value": …}]` → pipe to `fatsecret-chart`.
