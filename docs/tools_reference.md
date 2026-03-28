# FatSecret MCP Server - Tools Reference

Complete reference for all 20 MCP tools available in the FatSecret server.

## Overview

- **8 Public Tools** (No authentication required)
- **12 Authenticated Tools** (Require OAuth setup)
- **Total: 20 Tools**

---

## Public Tools (No Auth Required)

These tools work with `main_noauth.py` and don't require user authorization.

### Food Search & Nutrition

#### 1. `fatsecret_food_search`

Search for foods by name.

**Parameters:**
- `query` (string, required): Search query
- `max_results` (int, optional): Max results (default: 50)
- `page` (int, optional): Page number (default: 0)

**Returns:** List of foods with ID, name, brand, description

**Example:**
```
Search for "banana"
```

---

#### 2. `fatsecret_food_get`

Get detailed nutrition information for a specific food.

**Parameters:**
- `food_id` (string, required): Food ID from search

**Returns:** Complete nutrition facts with all serving sizes

**Example:**
```
Get nutrition facts for food ID 12345
```

---

#### 3. `fatsecret_food_autocomplete`

Get autocomplete suggestions for food search.

**Parameters:**
- `query` (string, required): Partial food name
- `max_results` (int, optional): Max suggestions (default: 10)

**Returns:** List of food name suggestions

**Example:**
```
Get suggestions for "chick"
```

---

#### 4. `fatsecret_food_search_v3`

Advanced food search with filters (same as v2 for now).

**Parameters:**
- `query` (string, required): Search query
- `max_results` (int, optional): Max results (default: 50)
- `page` (int, optional): Page number (default: 0)
- `region` (string, optional): Region code (default: "US")
- `language` (string, optional): Language code (default: "en")

**Returns:** List of foods

---

#### 5. `fatsecret_food_barcode_scan`

Lookup food by barcode (UPC/EAN).

**Parameters:**
- `barcode` (string, required): Barcode number

**Returns:** Food information if found

**Example:**
```
Scan barcode 012000161155
```

---

#### 6. `fatsecret_recipe_search`

Search for recipes by name or ingredients.

**Parameters:**
- `query` (string, required): Search query
- `max_results` (int, optional): Max results (default: 50)
- `page` (int, optional): Page number (default: 0)

**Returns:** List of recipes with name, description, URL, image

**Example:**
```
Search for chocolate cake recipes
```

---

#### 7. `fatsecret_recipe_get`

Get detailed recipe information.

**Parameters:**
- `recipe_id` (string, required): Recipe ID from search

**Returns:** Full recipe with ingredients, directions, nutrition per serving

**Example:**
```
Get recipe details for ID 12345
```

---

#### 8. `fatsecret_exercise_search`

Search for exercises (public search, no auth).

**Parameters:**
- `query` (string, required): Search query
- `max_results` (int, optional): Max results (default: 50)

**Returns:** List of exercises with ID and name

**Example:**
```
Search for "running" exercises
```

---

## Authenticated Tools (OAuth Required)

These tools require running `setup_oauth.py` first and using `main.py`.

### Food Diary

#### 9. `fatsecret_diary_get_entries`

Get all food diary entries for a date.

**Parameters:**
- `entry_date` (string, optional): Date YYYY-MM-DD (default: today)

**Returns:** List of entries with nutritional totals

**Example:**
```
Show my food diary for today
Get my diary entries for 2026-02-01
```

---

#### 10. `fatsecret_diary_get_month`

Get monthly summary of food diary.

**Parameters:**
- `year` (int, optional): Year (default: current year)
- `month` (int, optional): Month 1-12 (default: current month)

**Returns:** Daily totals for entire month

**Example:**
```
Show my food diary for February 2026
```

---

#### 11. `fatsecret_diary_add_entry`

Add a food entry to your diary.

**Parameters:**
- `food_id` (string, required): Food ID
- `serving_id` (string, required): Serving ID
- `meal` (string, required): "breakfast", "lunch", "dinner", "snack", "other"
- `number_of_units` (float, optional): Servings (default: 1.0)
- `entry_date` (string, optional): Date YYYY-MM-DD (default: today)

**Returns:** Entry ID

**Example:**
```
Log 2 scrambled eggs for breakfast
Add 1 banana to my snack diary
```

---

#### 12. `fatsecret_diary_edit_entry`

Edit an existing diary entry.

**Parameters:**
- `food_entry_id` (string, required): Entry ID to edit
- `serving_id` (string, optional): New serving ID
- `number_of_units` (float, optional): New serving size
- `meal` (string, optional): New meal

**Returns:** Success confirmation

**Example:**
```
Change entry 12345 to 2.5 servings
Move entry 12345 to lunch
```

---

#### 13. `fatsecret_diary_delete_entry`

Delete a food diary entry.

**Parameters:**
- `food_entry_id` (string, required): Entry ID to delete

**Returns:** Success confirmation

**Example:**
```
Delete diary entry 12345
```

---

### Exercise Tracking

#### 14. `fatsecret_exercise_get_entries`

Get exercise entries for a date.

**Parameters:**
- `entry_date` (string, optional): Date YYYY-MM-DD (default: today)

**Returns:** List of exercises with duration and calories burned

**Example:**
```
Show my exercises for today
```

---

#### 15. `fatsecret_exercise_get_month`

Get monthly exercise summary.

**Parameters:**
- `year` (int, optional): Year (default: current year)
- `month` (int, optional): Month 1-12 (default: current month)

**Returns:** Daily exercise totals

**Example:**
```
Show my exercise history for this month
```

---

#### 16. `fatsecret_exercise_add_entry`

Log an exercise activity.

**Parameters:**
- `exercise_id` (string, required): Exercise ID
- `minutes` (float, required): Duration in minutes
- `entry_date` (string, optional): Date YYYY-MM-DD (default: today)

**Returns:** Entry ID

**Example:**
```
Log 30 minutes of running
Add 45 minutes of swimming to my exercise log
```

---

#### 17. `fatsecret_exercise_edit_entry`

Edit an exercise entry.

**Parameters:**
- `exercise_entry_id` (string, required): Entry ID to edit
- `minutes` (float, required): New duration

**Returns:** Success confirmation

**Example:**
```
Change exercise entry 12345 to 45 minutes
```

---

### Weight Management

#### 18. `fatsecret_weight_update`

Record your weight for a date.

**Parameters:**
- `weight_kg` (float, required): Weight in kilograms
- `entry_date` (string, optional): Date YYYY-MM-DD (default: today)
- `comment` (string, optional): Note/comment

**Returns:** Success confirmation

**Example:**
```
Record my weight as 70.5 kg
Log my weight as 72 kg with comment "morning weight"
```

**Conversion:** 1 kg = 2.205 lbs

---

#### 19. `fatsecret_weight_get_month`

Get monthly weight history.

**Parameters:**
- `year` (int, optional): Year (default: current year)
- `month` (int, optional): Month 1-12 (default: current month)

**Returns:** List of weight entries with dates and comments

**Example:**
```
Show my weight history for this month
What was my weight trend in January?
```

---

## Common Workflows

### 1. Track a Meal

```
1. Search for food: "scrambled eggs"
2. Get nutrition: food ID from search
3. Add to diary: food ID + serving ID + meal + servings
4. View diary: check today's totals
```

**Example conversation:**
```
User: "Log 2 scrambled eggs for breakfast"
→ fatsecret_food_search("scrambled eggs")
→ fatsecret_food_get(food_id)
→ fatsecret_diary_add_entry(food_id, serving_id, "breakfast", 2.0)
→ fatsecret_diary_get_entries() to confirm
```

---

### 2. Track Exercise

```
1. Search exercise: "running"
2. Log activity: exercise ID + duration
3. View totals: check calories burned
```

**Example conversation:**
```
User: "I went running for 30 minutes"
→ fatsecret_exercise_search("running")
→ fatsecret_exercise_add_entry(exercise_id, 30.0)
→ fatsecret_exercise_get_entries() to confirm
```

---

### 3. Track Weight Progress

```
1. Record weight: weight in kg
2. View history: monthly trends
3. Calculate change: compare dates
```

**Example conversation:**
```
User: "My weight today is 70.5 kg"
→ fatsecret_weight_update(70.5)

User: "Show my weight trend this month"
→ fatsecret_weight_get_month()
→ Calculate: first_weight - last_weight
```

---

### 4. Find Recipes

```
1. Search recipes: by name or ingredient
2. Get details: recipe ID
3. View nutrition: calories per serving
```

**Example conversation:**
```
User: "Find me a healthy chocolate cake recipe"
→ fatsecret_recipe_search("healthy chocolate cake")
→ fatsecret_recipe_get(recipe_id)
→ Display: nutrition, ingredients, directions
```

---

## Error Handling

All tools return error messages in this format:

```json
{
  "error": "Error message here"
}
```

**Common errors:**
- "Query cannot be empty" - Missing required parameter
- "Invalid meal" - Meal must be breakfast/lunch/dinner/snack/other
- "Minutes must be positive" - Exercise duration must be > 0
- "Weight must be positive" - Weight must be > 0
- "No valid access token" - Need to run setup_oauth.py

## Rate Limits

FatSecret API has rate limits:
- **Free tier**: 500 calls/day
- **Paid tier**: Higher limits available

The server automatically handles:
- Token refresh
- Exponential backoff (coming in Phase 5)
- Request caching (coming in Phase 5)

## Tips

1. **Search before adding**: Always search for food first to get the correct ID
2. **Check servings**: Foods often have multiple serving sizes
3. **Use autocomplete**: Get spelling suggestions before full search
4. **Track consistently**: Log meals daily for accurate totals
5. **Monitor trends**: Use monthly views to track progress
6. **Barcode scanning**: Works best with packaged/branded products
7. **Exercise calories**: Automatically calculated based on your profile
8. **Weight units**: API uses kg, convert from lbs if needed (lbs / 2.205)

## Support

- API Documentation: https://platform.fatsecret.com/api
- Report Issues: https://github.com/yourusername/fatsecret-mcp/issues
