# テストおよび検証ガイド

このドキュメントでは、週間メニュープランナーD-1システムの包括的なテスト手順を提供します。

## ユニットテスト

### ローカルでのテスト実行

```bash
# テスト依存関係をインストール
pip install -r requirements.txt
pip install -r requirements-test.txt

# スキーマ検証テストを実行
PYTHONPATH=. python tests/test_intake_schema.py

# メニュージェネレーターテストを実行（モックAPIで）
PYTHONPATH=. python tests/test_menu_generator.py
```

### テストカバレッジ

#### スキーマ検証テスト
- ✅ 有効なデータでのIntakeDataモデル作成
- ✅ デフォルト値の適用
- ✅ フィールド検証（範囲、タイプ）
- ✅ JSONシリアライゼーション/デシリアライゼーション
- ✅ サンプルインテークデータの解析

#### メニュージェネレーターテスト
- ✅ YAMLからの設定読み込み
- ✅ JSONからのインテークデータ読み込み
- ✅ 設定のマージ（インテーク + デフォルト）
- ✅ 日本語コンテンツでのプロンプト生成
- ✅ 曜日名変換ユーティリティ

## 統合テスト

### GitHub Actionsワークフロー

GitHub Actionsで完全なワークフローをテスト：

1. **手動トリガーテスト**
   ```bash
   # GitHub Actionsタブに移動
   # "Weekly Menu Generation"をクリック
   # "Run workflow"をクリック
   # force_runをtrueに設定
   ```

2. **スケジュール実行テスト**
   ```bash
   # 日曜日 18:00 JST（09:00 UTC）を待つ
   # 自動実行のためにActionsタブをチェック
   ```

### 個別スクリプトテスト

#### 1. インテーク取得スクリプト
```bash
# 有効なgistでテスト
GITHUB_TOKEN=your_token GIST_ID=your_gist_id python scripts/fetch_intake.py

# 存在しないgistでテスト（適切に失敗するはず）
GITHUB_TOKEN=invalid GIST_ID=invalid python scripts/fetch_intake.py
```

#### 2. メニュー生成スクリプト
```bash
# インテークデータでテスト
cp data/intake_example.json data/intake.json
OPENAI_API_KEY=your_key python scripts/generate_menu.py

# インテークなしでテスト（デフォルトを使用）
rm data/intake.json
OPENAI_API_KEY=your_key python scripts/generate_menu.py
```

#### 3. Notion更新スクリプト
```bash
# Notion統合をテスト（生成されたメニューが必要）
NOTION_TOKEN=your_token NOTION_DATABASE_ID=your_db_id python scripts/notion_update.py
```

## Dify統合テスト

### Slackボットテスト

#### 1. 基本応答テスト
```
User: @menuplanner こんにちは
期待される結果: ボットが挨拶とメニュー作成の提案で応答
```

#### 2. スロット収集テスト
```
User: @menuplanner 今週の献立をお願いします
Bot: どちらの週の献立を作成しますか？
User: 来週
Bot: 何日分の夕食が必要ですか？
User: 5日分
Bot: 外泊や外食の予定はありますか？
User: 土日は外食
[会話フローを続ける...]
```

#### 3. JSON生成テスト
- 完全な会話がintake.jsonをgistに保存することを確認
- JSON構造がスキーマと一致することをチェック
- すべての収集されたデータを検証

### 会話フロー検証

#### 必須スロットテスト
- [ ] week_start収集と月曜日変換
- [ ] days_needed検証（1-7の範囲）
- [ ] away_days解析（日本語の曜日名）

#### オプションスロットテスト
- [ ] avoid_ingredients リスト解析
- [ ] max_cooking_time 検証
- [ ] cuisine_preferences 選択
- [ ] memo 自由テキスト処理
- [ ] guests_expected 数値解析

#### エラーハンドリングテスト
- [ ] 無効な日付入力の復旧
- [ ] gist保存中のネットワークエラー
- [ ] 不完全な会話の放棄
- [ ] 複数の同時ユーザー

## エンドツーエンドテスト

### 完全ワークフローテスト

1. **Dify会話**（金曜日/土曜日）
   - Slackで会話を開始
   - すべてのスロット収集を完了
   - JSONがgistに保存されることを確認

2. **GitHub Actions実行**（日曜日 18:00 JST）
   - intake.jsonが取得されることを確認
   - メニュー生成を確認
   - Notionページ作成をチェック

3. **結果検証**
   - Notionページに正しいコンテンツがある
   - 古いページがアーカイブされている
   - メニューがインテークの好みを尊重している

### AwayDays機能テスト

イシューで言及された特定の要件をテスト：

#### テストケース1: 週末外出
```json
{
  "days_needed": 5,
  "away_days": [5, 6],  // 土曜日、日曜日
  "week_start": "2024-01-15"
}
```

期待される結果:
- 月曜日-金曜日: 生成された食事
- 土曜日: "外食・外泊"
- 日曜日: "外食・外泊"

#### テストケース2: 日数削減
```json
{
  "days_needed": 3,
  "away_days": [],
  "week_start": "2024-01-15"
}
```

期待される結果:
- 月曜日-水曜日: 生成された食事
- 木曜日-日曜日: "お休み"

#### テストケース3: 週の途中で外出
```json
{
  "days_needed": 5,
  "away_days": [2, 3],  // 水曜日、木曜日
  "week_start": "2024-01-15"
}
```

期待される結果:
- 月曜日、火曜日: 生成された食事
- 水曜日、木曜日: "外食・外泊"
- 金曜日: 生成された食事
- 土曜日、日曜日: "お休み"

## パフォーマンステスト

### APIレート制限

#### OpenAI API
- 複数の迅速なリクエストでテスト
- レート制限処理を確認
- エラー復旧をチェック

#### Notion API
- 一括ページ操作をテスト
- ページネーション処理を確認
- 同時アクセスをチェック

#### GitHub API
- gist取得頻度をテスト
- 認証処理を確認
- ネットワークエラー復旧をチェック

## セキュリティテスト

### シークレット管理
- [ ] リポジトリコードにシークレットがない
- [ ] GitHub Secretsが適切に設定されている
- [ ] 環境変数がログに記録されない
- [ ] gistアクセス権限が正しい

### データプライバシー
- [ ] 個人データがGitHub Actionsでログに記録されない
- [ ] 会話ログにPIIが含まれない
- [ ] gistデータが適切にセキュアされている

## モニタリングとアラート

### GitHub Actionsモニタリング
```bash
# 最近のワークフロー実行をチェック
gh run list --workflow="Weekly Menu Generation"

# 特定の実行詳細を表示
gh run view <run_id>

# 失敗をチェック
gh run list --status=failure
```

### ログ分析
```bash
# ワークフローログをダウンロード
gh run download <run_id>

# 一般的なエラーをチェック
grep -i error *.log
grep -i "failed" *.log
```

## 一般的な問題のトラブルシューティング

### メニューが生成されない
1. GitHub Actionsログをチェック
2. OpenAI APIキーの有効性を確認
3. intake.jsonフォーマットをチェック
4. rules.yamlの構文を確認

### Notion更新失敗
1. Notionトークンの権限をチェック
2. データベースIDを確認
3. データベースプロパティスキーマをチェック
4. 統合アクセスをレビュー

### Difyボットが応答しない
1. Slackアプリの権限をチェック
2. Difyプラグイン設定を確認
3. Webhookエンドポイントをチェック
4. 会話フローロジックをレビュー

### インテークデータがない
1. gistアクセシビリティをチェック
2. GitHubトークンの権限を確認
3. gistファイル命名をレビュー
4. Dify HTTPリクエスト設定をチェック