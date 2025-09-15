# 環境変数設定ガイド

このドキュメントでは、週間メニュープランナーD-1システムに必要なすべての環境変数をリストアップします。

## GitHubリポジトリシークレット

GitHubリポジトリで以下のシークレットを設定してください（Settings → Secrets and variables → Actions）：

### 必須シークレット

#### OpenAI設定
```
OPENAI_API_KEY
説明: メニュー生成用のOpenAI APIキー
例: sk-...
取得場所: https://platform.openai.com/api-keys

OPENAI_MODEL (オプション)
説明: 生成に使用するOpenAIモデル
例: gpt-4, gpt-4-turbo, gpt-3.5-turbo
デフォルト: gpt-4
```

#### Notion設定
```
NOTION_TOKEN
説明: Notion統合トークン
例: secret_...
取得場所: https://www.notion.so/my-integrations

NOTION_DATABASE_ID
説明: メニューページ用NotionデータベースのID
例: 12345678-1234-1234-1234-123456789abc
取得場所: データベースのURLまたは共有メニューから
```

#### GitHub統合
```
GITHUB_TOKEN
説明: gist権限付きのGitHub個人アクセストークン
例: ghp_...
取得場所: https://github.com/settings/tokens
必要スコープ: gist

INTAKE_GIST_ID
説明: intake.jsonファイルを保存するGitHub GistのID
例: 1234567890abcdef1234567890abcdef
取得場所: プライベートgistを作成してURLからIDをコピー
```

## Notionデータベース設定

以下の正確なプロパティ名とタイプでNotionデータベースを作成してください：

| プロパティ名 | タイプ | 説明 |
|-------------|--------|------|
| Title | Title | ページタイトル（自動生成） |
| Week Start | Date | メニュー週の月曜日 |
| Generated At | Date | メニューが生成された日時 |
| Status | Select | オプション: "Current", "Archived" |
| Intake Used | Checkbox | intake.jsonが利用可能だったかどうか |

### データベーステンプレート
このテンプレートデータベースを複製できます：
[テンプレートデータベースへのリンクをここに配置]

## GitHub Gist設定

1. https://gist.github.com にアクセス
2. 新しいgistを作成（プライベート推奨）
3. 最初のファイルに `intake_example.json` と名前を付ける
4. `data/intake_example.json` からサンプルコンテンツを追加
5. URLからgist ID（長い英数字文字列）をコピー
6. このIDを `INTAKE_GIST_ID` シークレットとして追加

## ローカル開発用環境変数

プロジェクトルートに `.env` ファイルを作成（gitにコミットしない）：

```bash
# ローカル開発用.envファイル
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4
NOTION_TOKEN=your_notion_token_here
NOTION_DATABASE_ID=your_database_id_here
GITHUB_TOKEN=your_github_token_here
INTAKE_GIST_ID=your_gist_id_here
```

## 確認チェックリスト

### GitHub Actions設定
- [ ] すべてのシークレットがリポジトリ設定で設定されている
- [ ] GitHub Actionsがリポジトリで有効になっている
- [ ] ワークフローファイルが `.github/workflows/weekly-menu.yml` にある

### Notion設定
- [ ] 統合が作成されトークンがコピーされている
- [ ] データベースに正しいタイプのすべての必要プロパティがある
- [ ] 統合がデータベースにアクセスできる

### Gist設定
- [ ] Gistが作成されている（プライベート推奨）
- [ ] GitHubトークンにgist権限がある
- [ ] Gist IDが正しくアクセス可能

### Dify設定（準備ができたら）
- [ ] Difyアカウントが作成されている
- [ ] 正しい権限でSlackアプリが作成されている
- [ ] Dify Slackプラグインが設定されている
- [ ] チャットフローにgistを更新するHTTPリクエストが含まれている

## 環境変数のテスト

以下を実行して環境変数が適切に設定されているかテストできます：

```bash
# GitHub Actionsからのテスト
echo "環境変数をテスト中..."
echo "OpenAIキー: ${OPENAI_API_KEY:0:8}..."
echo "Notionトークン: ${NOTION_TOKEN:0:8}..."
echo "データベースID: ${NOTION_DATABASE_ID:0:8}..."
echo "GitHubトークン: ${GITHUB_TOKEN:0:8}..."
echo "Gist ID: $INTAKE_GIST_ID"
```

## セキュリティノート

- シークレットをリポジトリにコミットしない
- 本番環境ではGitHub Secretsを使用する
- ローカル開発では `.env` ファイルを使用（`.gitignore` に追加）
- 誤って公開された場合はトークンを再生成する
- ユーザーデータを保護するためプライベートgistを使用する