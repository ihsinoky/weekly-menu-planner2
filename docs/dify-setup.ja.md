# Dify ワークフロー設定ガイド

このドキュメントでは、会話形式でのインテーク収集を行うDify Slackボットの設定方法を詳しく説明します。

## Difyチャットフロー設計

### 概要
Difyチャットフローは、自然な会話を通じてユーザーの好みを収集し、構造化されたJSONファイルをGitHub Gistに出力する必要があります。

### スロット定義

Difyワークフローで以下の変数を作成してください：

#### 必須スロット
```yaml
week_start:
  type: string
  format: date (YYYY-MM-DD)
  description: "週の開始日（月曜日）"
  validation: 月曜日である必要があります
  prompt: "どちらの週の献立を作成しますか？（例：1月15日の週）"

days_needed:
  type: integer
  range: 1-7
  description: "食事を生成する日数"
  prompt: "何日分の夕食が必要ですか？（1-7日）"

away_days:
  type: array
  items: integer (0-6, where 0=Monday, 6=Sunday)
  description: "食事が不要な日"
  prompt: "外泊や外食の予定はありますか？曜日を教えてください。"
```

#### オプションスロット
```yaml
avoid_ingredients:
  type: array
  items: string
  description: "避けたい食材"
  prompt: "避けたい食材はありますか？アレルギーや苦手な食材があれば教えてください。"

max_cooking_time:
  type: integer
  range: 10-180
  description: "最大調理時間（分）"
  prompt: "調理時間の希望はありますか？平日は忙しいので短時間がよろしいでしょうか？"

cuisine_preferences:
  type: array
  items: string
  description: "好みの料理ジャンル"
  options: ["和食", "洋食", "中華", "イタリアン", "その他"]
  prompt: "お好みの料理ジャンルはありますか？"

dietary_restrictions:
  type: array
  items: string
  description: "食事制限"
  options: ["vegetarian", "vegan", "gluten-free", "low-sodium", "diabetic-friendly"]
  prompt: "食事制限はありますか？"

memo:
  type: string
  description: "追加のメモや特別なリクエスト"
  prompt: "その他、特別なご要望やメモがあれば教えてください。"

guests_expected:
  type: integer
  range: 0-10
  description: "予想される追加のゲスト数"
  prompt: "来客の予定はありますか？人数を教えてください。"
```

### 会話フローロジック

#### 1. 挨拶とコンテキスト設定
```
System: こんにちは！週間献立の作成をお手伝いします。
いくつか質問させていただきますので、お答えください。

まず、どちらの週の献立を作成しますか？
（例：来週、1月15日の週など）
```

#### 2. スロット収集戦略
- 未入力のスロットのみ質問する
- 自然な日本語会話を使用する
- 役に立つ場合は例を提供する
- 進む前に収集した情報を確認する

#### 3. バリデーションロジック
```python
# 週開始日の検証
def validate_week_start(date_string):
    date_obj = parse_date(date_string)
    if date_obj.weekday() != 0:  # 月曜日でない場合
        # その週の月曜日を計算
        monday = date_obj - timedelta(days=date_obj.weekday())
        return monday.strftime('%Y-%m-%d')
    return date_obj.strftime('%Y-%m-%d')

# 外出日の検証
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

### HTTPリクエスト設定

すべての必須スロットが入力されたら、DifyのHTTPリクエストツールを使用します：

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

### JSON出力テンプレート

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

## プロンプトテンプレート

### システムプロンプト
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

### 会話例

#### 例1: 基本フロー
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

#### 例2: 複雑なシナリオ
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

## テストチェックリスト

### Dify設定の確認
- [ ] Slackアプリの認証情報が適切に設定されている
- [ ] Dify Slackプラグインが動作している
- [ ] ボットがメンションとDMに応答する
- [ ] 会話フローが日本語入力を正しく処理する
- [ ] 必須スロットの検証が動作している
- [ ] GitHub GistへのHTTPリクエストが成功する

### スロット収集テスト
- [ ] 週開始日の計算（自動で月曜日に変換）
- [ ] 必要日数の検証（1-7の範囲）
- [ ] 外出日の解析（日本語の曜日名から数字へ）
- [ ] 食材リストの解析
- [ ] 調理時間の検証
- [ ] ゲスト数の処理
- [ ] メモフィールドの自由テキスト処理

### エラーハンドリング
- [ ] 無効な日付入力の処理
- [ ] Gist更新中のネットワークエラー
- [ ] 不完全なスロット収集からの復旧
- [ ] ユーザーの会話放棄
- [ ] 複数の同時会話

### 統合テスト
- [ ] 生成されたJSONがスキーマに対して検証される
- [ ] GitHub Actionsが新しいintake.jsonを取得する
- [ ] インテークデータでメニュー生成が動作する
- [ ] Notionページの作成が成功する
- [ ] 古いページのアーカイブが正しく動作する

## 高度な機能

### マルチターン確認
曖昧な入力に対するフォローアップ質問を実装：

```
User: 今週は忙しいです

Bot: お忙しいのですね。
     調理時間を短めにした方がよろしいでしょうか？
     それとも作り置きできるものがよろしいでしょうか？
```

### コンテキストメモリ
会話間でユーザーの好みを保存：

```
Bot: 前回はエビを避けるとおっしゃっていましたが、
     今回も同じでよろしいでしょうか？
```

### スマートデフォルト
ユーザーパターンから学習：

```
Bot: いつものように平日は30分以内、
     週末は少し手の込んだ料理でよろしいでしょうか？
```