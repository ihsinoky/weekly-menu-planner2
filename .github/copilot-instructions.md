# Copilot Instructions for Weekly Menu Planner

## Project Overview

This is a weekly menu planner system implementing the "D-1 Plan" architecture that combines conversational intake via Slack/Dify with automated menu generation using Python/GitHub Actions and Notion integration.

### Architecture
```
Slack User ↔ Dify Chatbot → GitHub Gist (intake.json) → GitHub Actions → OpenAI → Notion
```

## Core Technologies

- **Frontend**: Slack + Dify conversational AI
- **Backend**: Python scripts with GitHub Actions
- **APIs**: OpenAI GPT-4, Notion API, GitHub Gist API
- **Data**: YAML configuration, JSON intake files, Pydantic schemas
- **Language**: Primarily Japanese for user interface and content

## Project Structure

### Key Directories
- `.github/workflows/` - GitHub Actions automation
- `config/` - YAML configuration files with default rules
- `scripts/` - Core Python modules for menu generation pipeline
- `schemas/` - Pydantic data validation schemas
- `docs/` - Setup and usage documentation
- `tests/` - Test suite for validation

### Important Files
- `scripts/generate_menu.py` - Main OpenAI integration for menu generation
- `scripts/notion_update.py` - Notion database operations
- `scripts/fetch_intake.py` - GitHub Gist intake retrieval
- `schemas/intake_schema.py` - Data validation and type safety
- `config/rules.yaml` - Default configuration and fallback rules

## Coding Standards

### Python Code Style
- Use Pydantic models for all data validation and type safety
- Follow PEP 8 conventions
- Include comprehensive error handling with graceful degradation
- Use type hints for all functions and methods
- Prefer composition over inheritance for data structures

### Japanese Language Support
- All user-facing content should be in natural Japanese
- Use appropriate Japanese formatting for dates and days of the week
- Menu descriptions should sound natural and appetizing in Japanese
- Error messages and user guidance should be clear and polite in Japanese

### Configuration Management
- Use YAML files for human-readable configuration
- Validate all configuration with Pydantic schemas
- Provide sensible defaults for all optional parameters
- Support environment variable overrides for sensitive data

### API Integration Patterns
- Implement retry logic with exponential backoff for all external APIs
- Use proper authentication and rate limiting
- Log all API interactions for debugging
- Handle API failures gracefully with fallback mechanisms

## Development Guidelines

### When Working with Menu Generation
- Menu items should be realistic Japanese dishes with cooking times
- Consider seasonal ingredients and Japanese dietary preferences
- Handle "away days" (外泊/外食) by marking them as skip days
- Support flexible day counts (1-7 days) with proper remainder handling
- Include cooking time estimates and difficulty levels

### When Working with Notion Integration
- Always archive old menu pages before creating new ones
- Use structured properties: Title, Week Start, Generated At, Status, Intake Used
- Format content as rich text with proper Japanese day names
- Maintain page hierarchy and consistent naming conventions

### When Working with Conversational Flow
- Design natural Japanese conversation patterns
- Collect required slots: week_start, days_needed, away_days
- Support optional preferences: avoid_ingredients, max_cooking_time, etc.
- Validate user input and provide helpful correction guidance
- Output structured JSON to GitHub Gist with idempotent naming

### Testing Approach
- Write unit tests for all Pydantic schemas
- Test API integrations with mock data
- Validate Japanese text formatting and date handling
- Test error scenarios and fallback mechanisms
- Include end-to-end workflow validation

## Common Patterns

### Error Handling
```python
try:
    # API operation
    result = api_call()
except APIError as e:
    logger.error(f"API failed: {e}")
    # Graceful fallback
    result = default_behavior()
```

### Data Validation
```python
from pydantic import BaseModel, validator

class IntakeData(BaseModel):
    week_start: str
    days_needed: int
    
    @validator('days_needed')
    def validate_days(cls, v):
        if not 1 <= v <= 7:
            raise ValueError('days_needed must be 1-7')
        return v
```

### Configuration Loading
```python
import yaml
from pathlib import Path

def load_config(file_path: str):
    with open(Path(__file__).parent / file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)
```

## Environment Variables

Always use these secret names in GitHub Actions:
- `OPENAI_API_KEY` - OpenAI API access
- `NOTION_TOKEN` - Notion integration token
- `NOTION_DATABASE_ID` - Target Notion database
- `GITHUB_TOKEN` - GitHub API access
- `INTAKE_GIST_ID` - Gist for intake.json storage

## Documentation Standards

- Include setup instructions in Japanese and English
- Provide conversation examples for user guidance
- Document all configuration options and their effects
- Include troubleshooting guides for common issues
- Maintain API integration examples and error scenarios

## Security Considerations

- Never log or expose API keys or tokens
- Use GitHub Secrets for all sensitive configuration
- Validate all user inputs to prevent injection attacks
- Implement proper rate limiting for external API calls
- Handle personal data (dietary restrictions, preferences) carefully

## Performance Guidelines

- Cache API responses when appropriate
- Use batch operations for Notion database updates
- Implement efficient JSON parsing and validation
- Minimize API calls through smart data reuse
- Log performance metrics for optimization

## Deployment Practices

- Test all changes in development environment first
- Validate GitHub Actions workflows before merging
- Ensure proper error handling for production scenarios
- Monitor API usage and rate limits
- Maintain backup strategies for configuration data