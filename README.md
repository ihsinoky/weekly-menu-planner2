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

### 1. 必要な環境変数

GitHub リポジトリの Secrets に以下を設定してください：

```
OPENAI_API_KEY         # OpenAI API キー
NOTION_TOKEN          # Notion インテグレーショントークン
NOTION_DATABASE_ID    # Notion データベース ID
GITHUB_TOKEN          # GitHub パーソナルアクセストークン
INTAKE_GIST_ID        # intake.json を保存する GitHub Gist ID
```

### 2. Notion データベース設定

Notion で以下のプロパティを持つデータベースを作成してください：

| プロパティ名 | タイプ | 説明 |
|------------|------|------|
| Title | タイトル | ページタイトル |
| Week Start | 日付 | 週の開始日（月曜日） |
| Generated At | 日付 | 生成日時 |
| Status | セレクト | Current/Archived |
| Intake Used | チェックボックス | intake.json が使用されたか |

### 3. GitHub Gist 作成

1. GitHub で新しい Gist を作成（プライベート推奨）
2. ファイル名を `intake_example.json` として以下の内容で作成：

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

3. Gist の ID（URL の最後の部分）を `INTAKE_GIST_ID` に設定

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