# Dify Workflow Setup Guide

This document provides detailed instructions for setting up the Dify Slack bot for conversational intake collection.

## Dify Chatflow Design

### Overview
The Dify chatflow should collect user preferences through natural conversation and output a structured JSON file to GitHub Gist.

### Slot Definitions

Create the following variables in your Dify workflow:

#### Required Slots
```yaml
week_start:
  type: string
  format: date (YYYY-MM-DD)
  description: "Start date of the week (Monday)"
  validation: Must be a Monday
  prompt: "どちらの週の献立を作成しますか？（例：1月15日の週）"

days_needed:
  type: integer
  range: 1-7
  description: "Number of days to generate meals for"
  prompt: "何日分の夕食が必要ですか？（1-7日）"

away_days:
  type: array
  items: integer (0-6, where 0=Monday, 6=Sunday)
  description: "Days when no meals are needed"
  prompt: "外泊や外食の予定はありますか？曜日を教えてください。"
```

#### Optional Slots
```yaml
avoid_ingredients:
  type: array
  items: string
  description: "Ingredients to avoid"
  prompt: "避けたい食材はありますか？アレルギーや苦手な食材があれば教えてください。"

max_cooking_time:
  type: integer
  range: 10-180
  description: "Maximum cooking time in minutes"
  prompt: "調理時間の希望はありますか？平日は忙しいので短時間がよろしいでしょうか？"

cuisine_preferences:
  type: array
  items: string
  description: "Preferred cuisine types"
  options: ["和食", "洋食", "中華", "イタリアン", "その他"]
  prompt: "お好みの料理ジャンルはありますか？"

dietary_restrictions:
  type: array
  items: string
  description: "Dietary restrictions"
  options: ["vegetarian", "vegan", "gluten-free", "low-sodium", "diabetic-friendly"]
  prompt: "食事制限はありますか？"

memo:
  type: string
  description: "Additional notes or special requests"
  prompt: "その他、特別なご要望やメモがあれば教えてください。"

guests_expected:
  type: integer
  range: 0-10
  description: "Number of additional guests expected"
  prompt: "来客の予定はありますか？人数を教えてください。"
```

### Conversation Flow Logic

#### 1. Greeting and Context Setting
```
System: こんにちは！週間献立の作成をお手伝いします。
いくつか質問させていただきますので、お答えください。

まず、どちらの週の献立を作成しますか？
（例：来週、1月15日の週など）
```

#### 2. Slot Filling Strategy
- Ask only for unfilled slots
- Use natural Japanese conversation
- Provide examples when helpful
- Confirm collected information before proceeding

#### 3. Validation Logic
```python
# Week start validation
def validate_week_start(date_string):
    date_obj = parse_date(date_string)
    if date_obj.weekday() != 0:  # Not Monday
        # Calculate the Monday of that week
        monday = date_obj - timedelta(days=date_obj.weekday())
        return monday.strftime('%Y-%m-%d')
    return date_obj.strftime('%Y-%m-%d')

# Away days validation
def validate_away_days(day_strings):
    day_mapping = {
        "月曜": 0, "火曜": 1, "水曜": 2, "木曜": 3, 
        "金曜": 4, "土曜": 5, "日曜": 6
    }
    result = []
    for day in day_strings:
        for jp_day, num in day_mapping.items():
            if jp_day in day:
                result.append(num)
    return result
```

### HTTP Request Configuration

When all required slots are filled, use Dify's HTTP Request tool:

```http
PATCH https://api.github.com/gists/{{GIST_ID}}
Authorization: token {{GITHUB_TOKEN}}
Content-Type: application/json

Body:
{
  "files": {
    "intake_{{week_start}}.json": {
      "content": "{{json_output}}"
    }
  }
}
```

### JSON Output Template

```json
{
  "week_start": "{{week_start}}",
  "timestamp": "{{current_timestamp}}",
  "days_needed": {{days_needed}},
  "away_days": {{away_days}},
  "avoid_ingredients": {{avoid_ingredients}},
  "max_cooking_time": {{max_cooking_time}},
  "priority_recipe_sites": ["cookpad.com", "kurashiru.com", "recipe.rakuten.co.jp"],
  "cuisine_preferences": {{cuisine_preferences}},
  "dietary_restrictions": {{dietary_restrictions}},
  "memo": "{{memo}}",
  "guests_expected": {{guests_expected}},
  "special_occasions": [],
  "user_id": "{{slack_user_id}}",
  "conversation_id": "{{conversation_id}}"
}
```

## Prompt Templates

### System Prompt
```
あなたは日本の家庭向け献立プランナーのアシスタントです。
ユーザーから週間献立作成に必要な情報を自然な会話で収集してください。

収集すべき情報：
1. 対象週（必須）
2. 必要日数（必須）
3. 外泊日
4. 避けたい食材
5. 調理時間の希望
6. 料理ジャンルの好み
7. 食事制限
8. 特記事項
9. 来客予定

会話のガイドライン：
- 親しみやすく丁寧な関西弁で対応
- 一度に多くの質問をせず、1-2項目ずつ確認
- ユーザーの回答に共感を示す
- 必要な情報が集まったら確認してから保存する
```

### Conversation Examples

#### Example 1: Basic Flow
```
Bot: こんにちは！今週の献立作成をお手伝いします。
     どちらの週の献立を作成しますか？

User: 来週お願いします

Bot: 来週ですね！何日分の夕食が必要でしょうか？

User: 5日分でお願いします

Bot: 5日分承知しました。外泊や外食の予定はありますか？

User: 土日は実家に帰ります

Bot: 土日は外食ということですね。
     避けたい食材やアレルギーはありますか？

User: 特にありません

Bot: わかりました。調理時間はいかがでしょうか？
     平日はお忙しいですか？

User: 平日は30分くらいで作れるものがいいです

Bot: 30分以内ですね。承知しました！
     
     確認させていただきます：
     - 対象週: 来週（1月15日週）
     - 必要日数: 5日分
     - 外食日: 土曜日、日曜日
     - 避ける食材: なし
     - 調理時間: 30分以内
     
     この内容で献立を作成してよろしいでしょうか？

User: はい、お願いします

Bot: ありがとうございます！献立データを保存しました。
     日曜日の夜にNotionに新しい献立が反映されます。
     楽しみにお待ちください！
```

#### Example 2: Complex Scenario
```
Bot: こんにちは！献立作成をお手伝いします。

User: 今度の週、来客があるので相談したいです

Bot: 来客があるのですね！素敵ですね。
     何名様の予定でしょうか？

User: 3名です。金曜日の夜に友人が来ます

Bot: 3名様で金曜日ですね。
     まず、その週は何日分の夕食が必要でしょうか？

User: 一週間分お願いします

Bot: 一週間分承知しました。
     金曜日は来客用に少し豪華にした方がよろしいでしょうか？

User: そうですね。和食でお願いします

Bot: 和食で来客向けですね。
     他に避けたい食材やアレルギーはありますか？
     友人の方の分も含めて教えてください。

User: エビアレルギーの人がいるので、エビは避けてください

Bot: エビは避けるということですね。承知しました。
     
     確認させていただきます：
     - 対象週: 来週（1月15日週）
     - 必要日数: 7日分
     - 来客予定: 金曜日に3名（和食希望）
     - 避ける食材: エビ
     
     この内容でよろしいでしょうか？

User: はい、お願いします

Bot: ありがとうございます！
     金曜日は来客向けの和食、他の日はバランス良く
     献立を作成いたします。日曜日に反映されますね！
```

## Testing Checklist

### Dify Setup Verification
- [ ] Slack app credentials properly configured
- [ ] Dify Slack plugin working
- [ ] Bot responds to mentions and DMs
- [ ] Conversation flow handles Japanese input correctly
- [ ] Required slots validation working
- [ ] HTTP request to GitHub Gist succeeds

### Slot Collection Testing
- [ ] Week start calculation (auto-convert to Monday)
- [ ] Days needed validation (1-7)
- [ ] Away days parsing (Japanese day names to numbers)
- [ ] Ingredient list parsing
- [ ] Cooking time validation
- [ ] Guest count handling
- [ ] Memo field free text handling

### Error Handling
- [ ] Invalid date input handling
- [ ] Network error during Gist update
- [ ] Incomplete slot collection recovery
- [ ] User conversation abandonment
- [ ] Multiple concurrent conversations

### Integration Testing
- [ ] Generated JSON validates against schema
- [ ] GitHub Actions picks up new intake.json
- [ ] Menu generation works with intake data
- [ ] Notion page creation succeeds
- [ ] Old page archival works correctly

## Advanced Features

### Multi-turn Clarification
Implement follow-up questions for ambiguous input:

```
User: 今週は忙しいです

Bot: お忙しいのですね。
     調理時間を短めにした方がよろしいでしょうか？
     それとも作り置きできるものがよろしいでしょうか？
```

### Context Memory
Store user preferences across conversations:

```
Bot: 前回はエビを避けるとおっしゃっていましたが、
     今回も同じでよろしいでしょうか？
```

### Smart Defaults
Learn from user patterns:

```
Bot: いつものように平日は30分以内、
     週末は少し手の込んだ料理でよろしいでしょうか？
```