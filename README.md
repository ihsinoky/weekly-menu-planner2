# Weekly Menu Planner (D-1 Plan)

週次献立自動生成システムの D-1 プラン実装です。Slack での自然な対話による条件取得を Dify に任せ、献立生成と Notion 更新は Python/GitHub Actions パイプラインで実行します。

## 🏗️ アーキテクチャ

```
Slack（ユーザー） ↔ Dify Slackボット（会話・条件取得）
                             ↓ JSON出力（intake.json）
                              ─────────────→ GitHub Gist
                                                  ↓ 週次取得
GitHub Actions（cron） → Python → OpenAI API → Notion DB
```

## 🚀 セットアップ

### 1. 必要な環境変数の取得と設定

#### OpenAI API キーの取得

1. [OpenAI Platform](https://platform.openai.com/) にアクセス
2. アカウントにログインまたは新規作成
3. 右上のアカウントメニュー → "View API keys" をクリック
4. "Create new secret key" をクリックしてAPIキーを生成
5. キーをコピーして安全な場所に保存（一度しか表示されません）

#### Notion インテグレーションの設定

1. [Notion Developers](https://www.notion.so/my-integrations) にアクセス
2. "New integration" をクリック
3. インテグレーション名を入力（例：「Weekly Menu Planner」）
4. ワークスペースを選択して "Submit" をクリック
5. **Internal Integration Token** をコピーして保存
6. 献立用データベースを作成後、そのページで：
   - 右上の "Share" をクリック
   - 作成したインテグレーションを招待
   - "Invite" をクリック

#### GitHub パーソナルアクセストークンの作成

1. GitHub にログイン後、右上のプロフィール → "Settings"
2. 左メニューの "Developer settings" → "Personal access tokens" → "Tokens (classic)"
3. "Generate new token" → "Generate new token (classic)" をクリック
4. 以下の設定で作成：
   - **Note**: Weekly Menu Planner
   - **Expiration**: 90 days（お好みで調整）
   - **Scopes**: `gist` にチェック
5. "Generate token" をクリックしてトークンをコピー

#### GitHub リポジトリの Secrets 設定

1. このリポジトリの **Settings** タブをクリック
2. 左メニューの **Secrets and variables** → **Actions** をクリック
3. **New repository secret** をクリックして以下を順次追加：

```
Name: OPENAI_API_KEY
Secret: [取得したOpenAI APIキー]

Name: OPENAI_MODEL
Secret: gpt-4 (または gpt-4-turbo, gpt-3.5-turbo)

Name: NOTION_TOKEN
Secret: [取得したNotion Integration Token]

Name: NOTION_DATABASE_ID
Secret: [後で作成するデータベースID]

Name: GITHUB_TOKEN
Secret: [作成したPersonal Access Token]

Name: INTAKE_GIST_ID
Secret: [後で作成するGist ID]
```

### 2. Notion データベース設定

#### データベースの作成

1. Notion で新しいページを作成
2. `/table` と入力してデータベースを作成
3. データベース名を「週間献立」などに変更
4. 以下のプロパティを追加：

| プロパティ名 | タイプ | 説明 | 設定方法 |
|------------|------|------|---------|
| Title | タイトル | ページタイトル | デフォルトで存在 |
| Week Start | 日付 | 週の開始日（月曜日） | 右上の "+" → "Date" |
| Generated At | 日付 | 生成日時 | 右上の "+" → "Date" |
| Status | セレクト | Current/Archived | 右上の "+" → "Select" |
| Intake Used | チェックボックス | intake.json が使用されたか | 右上の "+" → "Checkbox" |

#### Status セレクトオプションの設定

1. Status プロパティをクリック
2. "Current" オプションを追加（色：緑）
3. "Archived" オプションを追加（色：グレー）

#### データベース ID の取得

1. データベースページのURLをコピー
2. URLは以下の形式です：
   ```
   https://www.notion.so/[ワークスペース]/[データベース名]-[データベースID]?v=[ビューID]
   ```
3. データベース ID は URL の `[データベースID]` 部分（32文字のハイフンあり文字列）
4. 取得した ID を GitHub Secrets の `NOTION_DATABASE_ID` に設定

### 3. GitHub Gist の作成

#### 新しい Gist の作成

1. [GitHub Gist](https://gist.github.com/) にアクセス
2. 以下の設定で Gist を作成：
   - **Filename**: `intake_example.json`
   - **Content**: 以下のJSON内容をコピー＆ペースト

```json
{
  "week_start": "2024-01-15",
  "timestamp": "2024-01-14T10:30:00+09:00",
  "days_needed": 7,
  "away_days": [],
  "avoid_ingredients": [],
  "max_cooking_time": 60,
  "priority_recipe_sites": ["cookpad.com", "kurashiru.com"],
  "cuisine_preferences": ["和食", "洋食", "中華"],
  "dietary_restrictions": [],
  "memo": null,
  "guests_expected": 0,
  "special_occasions": [],
  "user_id": null,
  "conversation_id": null
}
```

3. **Create secret gist** をクリック（プライベート推奨）

#### Gist ID の取得

1. 作成した Gist のページの URL を確認
2. URL 形式：`https://gist.github.com/[ユーザー名]/[GistID]`
3. `[GistID]` の部分（32文字の英数字）をコピー
4. GitHub Secrets の `INTAKE_GIST_ID` に設定

#### セットアップ確認

すべての環境変数が設定できたら、GitHub Actions の手動実行でテストしてください：

1. リポジトリの **Actions** タブをクリック
2. **Weekly Menu Generation** ワークフローを選択
3. **Run workflow** をクリックして手動実行
4. 実行ログでエラーがないか確認

### 4. GitHub Actions ワークフローの設定

GitHub リポジトリの Secrets に以下を設定してください：

```
OPENAI_API_KEY         # OpenAI API キー
OPENAI_MODEL          # 使用するOpenAIモデル（デフォルト: gpt-4）
NOTION_TOKEN          # Notion インテグレーショントークン
NOTION_DATABASE_ID    # Notion データベース ID
GITHUB_TOKEN          # GitHub パーソナルアクセストークン
INTAKE_GIST_ID        # intake.json を保存する GitHub Gist ID
```

## 📱 Dify Slack ボット設定

### 1. Slack アプリ作成

1. [Slack API](https://api.slack.com/apps) で新しいアプリを作成
2. **OAuth & Permissions** で以下のスコープを追加：
   - `app_mentions:read`
   - `chat:write`
   - `im:read`
   - `im:write`
3. **Event Subscriptions** を有効化し、以下のイベントを購読：
   - `app_mention`
   - `message.im`
4. Bot User OAuth Token を取得

### 2. Dify アカウント設定

1. [Dify](https://dify.ai) でアカウント作成
2. 新しい Chatflow または Agent アプリを作成
3. Slack プラグインを設定（Bot Token と Signing Secret を入力）

### 3. Dify チャットフロー設計

以下のスロットを定義してください：

#### 必須スロット
- `week_start`: 献立を作成する週の開始日（月曜日）
- `days_needed`: 必要な日数（1-7）
- `away_days`: 外泊日（月曜=0, 日曜=6 の配列）

#### オプションスロット
- `avoid_ingredients`: 避けたい食材のリスト
- `max_cooking_time`: 最大調理時間（分）
- `cuisine_preferences`: 好みの料理ジャンル
- `dietary_restrictions`: 食事制限
- `memo`: 特記事項
- `guests_expected`: 来客予定人数

### 4. JSON 出力設定

すべてのスロットが埋まったら、Dify の HTTP Request ツールで以下を実行：

```http
POST https://api.github.com/gists/{GIST_ID}/files
Authorization: token {GITHUB_TOKEN}
Content-Type: application/json

{
  "files": {
    "intake_{week_start}.json": {
      "content": "{スロットデータをJSON形式で}"
    }
  }
}
```

## 💬 Slack での使い方

### 基本的な会話例

```
ユーザー: @献立ボット 今週の献立をお願いします

ボット: こんにちは！今週の献立を作成させていただきますね。
いくつか質問させてください。

今週は何日分の夕食が必要ですか？（1-7日）

ユーザー: 5日分でお願いします

ボット: 5日分ですね。外泊や外食の予定はありますか？
もしあれば、曜日を教えてください（例：土曜日、日曜日）

ユーザー: 土日は実家に帰るので外食です

ボット: 承知しました。避けたい食材はありますか？
アレルギーや苦手な食材があれば教えてください。

ユーザー: エビとカニは避けてください

ボット: わかりました。調理時間の希望はありますか？
平日は忙しいので短時間がよろしいでしょうか？

ユーザー: 平日は30分以内でお願いします

ボット: 承知しました！以下の内容で献立を作成いたします：
- 必要日数: 5日分
- 外食日: 土曜日、日曜日
- 避ける食材: エビ、カニ
- 調理時間: 30分以内

この内容で生成を開始しますね。日曜日の夜に Notion に反映されます！
```

### 高度な使い方

特記事項がある場合：

```
ユーザー: 今週は来客があります

ボット: 来客の予定があるのですね。何名様の予定でしょうか？

ユーザー: 3名です。金曜日の夜に予定しています

ボット: 3名様の来客ですね。金曜日は少し豪華な料理にいたしましょうか？
何かご希望の料理ジャンルはありますか？

ユーザー: 和食でお願いします

ボット: 承知しました。和食で来客向けの献立を金曜日に組み込みますね。
```

## 🔧 トラブルシューティング

### よくある問題

#### 1. ボットが反応しない
- Slack アプリの Event Subscriptions が正しく設定されているか確認
- Dify の Slack プラグイン設定を再確認
- Bot Token の権限が適切か確認

#### 2. 献立が生成されない
- GitHub Actions のログを確認
- OpenAI API キーが有効か確認
- intake.json が正しく Gist に保存されているか確認

#### 3. Notion に反映されない
- Notion インテグレーションの権限を確認
- データベース ID が正しいか確認
- データベースのプロパティ名が仕様と一致しているか確認

### ログの確認方法

1. **GitHub Actions ログ**: リポジトリの Actions タブで実行履歴を確認
2. **Dify ログ**: Dify アプリの Logs セクションで会話履歴を確認
3. **Slack ログ**: Slack アプリの Event Subscriptions でリクエスト履歴を確認

### エラー対処

#### intake.json が見つからない場合
システムは自動的に `config/rules.yaml` のデフォルト設定で献立を生成します。

#### API レート制限に達した場合
- OpenAI API: 使用量を確認し、プランをアップグレードするか時間をあけて再実行
- Notion API: リクエスト頻度を下げるか、時間をあけて再実行

## ⚙️ 設定のカスタマイズ

### OpenAI モデルの変更

使用する OpenAI モデルを変更するには、GitHub Actions の環境変数 `OPENAI_MODEL` を設定してください：

```
OPENAI_MODEL=gpt-4-turbo    # より高性能なモデル
OPENAI_MODEL=gpt-3.5-turbo  # より経済的なモデル
```

設定しない場合は、デフォルトで `gpt-4` が使用されます。

### rules.yaml のカスタマイズ

`config/rules.yaml` ファイルを編集することで、デフォルトの献立生成設定をカスタマイズできます：

#### 基本設定

```yaml
default_settings:
  days_needed: 5              # 平日のみの場合は5に変更
  away_days: [5, 6]          # 土日を外食日に設定
  avoid_ingredients: ["海老", "蟹"]  # アレルギー食材を設定
  max_cooking_time: 30        # 忙しい平日は30分に短縮
  priority_recipe_sites:
    - "cookpad.com"           # よく使うレシピサイトを優先
    - "kurashiru.com"
    - "delishkitchen.tv"      # お好みのサイトを追加
```

#### 料理ジャンルの調整

```yaml
recipe_preferences:
  cuisine_types:
    - "和食"                  # 和食中心にしたい場合
    - "洋食"
  difficulty_level: "easy"    # 簡単な料理のみ
  variety_preference: "medium" # バラエティを控えめに
```

#### 栄養バランスの重視度

```yaml
nutrition:
  consider_balance: true
  protein_sources:
    - "魚"                   # 魚中心の食事にしたい場合
    - "豆腐・大豆製品"
  vegetable_emphasis: true    # 野菜を多めに
```

#### 特殊ルール

```yaml
special_rules:
  avoid_consecutive_similar: true   # 連日同じ系統を避ける
  weekend_special: true            # 週末は少し豪華に
  prep_time_consideration: true    # 平日は準備時間を考慮
```

### カスタマイズ例

#### ヘルシー志向の設定

```yaml
default_settings:
  days_needed: 7
  max_cooking_time: 45
  dietary_preferences: ["低カロリー", "野菜多め"]

nutrition:
  protein_sources:
    - "魚"
    - "鶏胸肉"
    - "豆腐・大豆製品"
  vegetable_emphasis: true
```

#### 時短重視の設定

```yaml
default_settings:
  max_cooking_time: 20
  priority_recipe_sites:
    - "kurashiru.com"        # 時短レシピが豊富
    - "delishkitchen.tv"

recipe_preferences:
  difficulty_level: "easy"
  
special_rules:
  prep_time_consideration: true
```

#### ファミリー向けの設定

```yaml
default_settings:
  avoid_ingredients: ["辛いもの", "臭いの強いもの"]
  
recipe_preferences:
  cuisine_types:
    - "和食"
    - "洋食"
    - "子供向け"
  variety_preference: "high"

special_rules:
  weekend_special: true        # 週末は家族で楽しめる料理
```

**注意**: `rules.yaml` を変更した場合、次回の自動実行時から新しい設定が適用されます。すぐに反映したい場合は、GitHub Actions を手動実行してください。

## 📊 設定ファイル詳細

### config/rules.yaml
デフォルト設定とフォールバック値を定義します。

### schemas/intake_schema.py
intake.json の構造と検証ルールを定義します。

## 🔄 実行フロー

1. **週次実行**: 毎週日曜日 18:00 JST に GitHub Actions が自動実行
2. **intake 取得**: GitHub Gist から最新の intake.json を取得
3. **設定マージ**: intake データと rules.yaml をマージ
4. **献立生成**: OpenAI API で日本語の献立を生成
5. **Notion 更新**: 新しいページを作成し、古いページをアーカイブ

## 🎯 今後の拡張予定

- 在庫管理との連携
- Google Calendar 統合
- 栄養バランス分析
- レシピサイトからの詳細情報取得
- Web UI の追加

## 📝 ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。