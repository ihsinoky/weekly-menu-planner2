# Environment Variables Setup Guide

This document lists all required environment variables for the Weekly Menu Planner D-1 system.

## GitHub Repository Secrets

Set the following secrets in your GitHub repository (Settings → Secrets and variables → Actions):

### Required Secrets

#### OpenAI Configuration
```
OPENAI_API_KEY
Description: OpenAI API key for menu generation
Example: sk-...
Where to get: https://platform.openai.com/api-keys

OPENAI_MODEL (Optional)
Description: OpenAI model to use for generation
Example: gpt-4, gpt-4-turbo, gpt-3.5-turbo
Default: gpt-4
```

#### Notion Configuration
```
NOTION_TOKEN
Description: Notion integration token
Example: secret_...
Where to get: https://www.notion.so/my-integrations

NOTION_DATABASE_ID
Description: ID of the Notion database for menu pages
Example: 12345678-1234-1234-1234-123456789abc
Where to get: From the database URL or share menu
```

#### GitHub Integration
```
GITHUB_TOKEN
Description: GitHub personal access token with gist permissions
Example: ghp_...
Where to get: https://github.com/settings/tokens
Required scopes: gist

INTAKE_GIST_ID
Description: ID of the GitHub Gist for storing intake.json files
Example: 1234567890abcdef1234567890abcdef
Where to get: Create a private gist and copy the ID from URL
```

## Notion Database Setup

Create a Notion database with these exact property names and types:

| Property Name | Type | Description |
|---------------|------|-------------|
| Title | Title | Page title (auto-generated) |
| Week Start | Date | Monday of the menu week |
| Generated At | Date | When the menu was generated |
| Status | Select | Options: "Current", "Archived" |
| Intake Used | Checkbox | Whether intake.json was available |

### Database Template
You can duplicate this template database:
[Link to template database would go here]

## GitHub Gist Setup

1. Go to https://gist.github.com
2. Create a new gist (private recommended)
3. Name the first file `intake_example.json`
4. Add the example content from `data/intake_example.json`
5. Copy the gist ID from the URL (the long alphanumeric string)
6. Add this ID as `INTAKE_GIST_ID` secret

## Environment Variables for Local Development

Create a `.env` file in the project root (not committed to git):

```bash
# .env file for local development
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4
NOTION_TOKEN=your_notion_token_here
NOTION_DATABASE_ID=your_database_id_here
GITHUB_TOKEN=your_github_token_here
INTAKE_GIST_ID=your_gist_id_here
```

## Verification Checklist

### GitHub Actions Setup
- [ ] All secrets are set in repository settings
- [ ] GitHub Actions is enabled for the repository
- [ ] Workflow file is in `.github/workflows/weekly-menu.yml`

### Notion Setup
- [ ] Integration is created and token is copied
- [ ] Database has all required properties with correct types
- [ ] Integration has access to the database

### Gist Setup
- [ ] Gist is created (private recommended)
- [ ] GitHub token has gist permissions
- [ ] Gist ID is correct and accessible

### Dify Setup (when ready)
- [ ] Dify account created
- [ ] Slack app created with correct permissions
- [ ] Dify Slack plugin configured
- [ ] Chatflow includes HTTP request to update gist

## Testing Environment Variables

You can test if environment variables are properly set by running:

```bash
# Test from GitHub Actions
echo "Testing environment variables..."
echo "OpenAI key: ${OPENAI_API_KEY:0:8}..."
echo "Notion token: ${NOTION_TOKEN:0:8}..."
echo "Database ID: ${NOTION_DATABASE_ID:0:8}..."
echo "GitHub token: ${GITHUB_TOKEN:0:8}..."
echo "Gist ID: $INTAKE_GIST_ID"
```

## Security Notes

- Never commit secrets to the repository
- Use GitHub Secrets for production
- Use `.env` files for local development (add to `.gitignore`)
- Regenerate tokens if they are accidentally exposed
- Use private gists to protect user data