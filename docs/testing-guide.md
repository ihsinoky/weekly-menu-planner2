# Testing and Validation Guide

This document provides comprehensive testing procedures for the Weekly Menu Planner D-1 system.

## Unit Tests

### Running Tests Locally

```bash
# Install test dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt

# Run schema validation tests
PYTHONPATH=. python tests/test_intake_schema.py

# Run menu generator tests (with mocked APIs)
PYTHONPATH=. python tests/test_menu_generator.py
```

### Test Coverage

#### Schema Validation Tests
- ✅ IntakeData model creation with valid data
- ✅ Default values application
- ✅ Field validation (ranges, types)
- ✅ JSON serialization/deserialization
- ✅ Example intake data parsing

#### Menu Generator Tests
- ✅ Configuration loading from YAML
- ✅ Intake data loading from JSON
- ✅ Settings merging (intake + defaults)
- ✅ Prompt generation with Japanese content
- ✅ Day name conversion utilities

## Integration Testing

### GitHub Actions Workflow

Test the complete workflow in GitHub Actions:

1. **Manual Trigger Test**
   ```bash
   # Go to GitHub Actions tab
   # Click "Weekly Menu Generation"
   # Click "Run workflow"
   # Set force_run to true
   ```

2. **Scheduled Run Test**
   ```bash
   # Wait for Sunday 18:00 JST (09:00 UTC)
   # Check Actions tab for automatic execution
   ```

### Individual Script Testing

#### 1. Fetch Intake Script
```bash
# Test with valid gist
GITHUB_TOKEN=your_token GIST_ID=your_gist_id python scripts/fetch_intake.py

# Test with missing gist (should fail gracefully)
GITHUB_TOKEN=invalid GIST_ID=invalid python scripts/fetch_intake.py
```

#### 2. Menu Generation Script
```bash
# Test with intake data
cp data/intake_example.json data/intake.json
OPENAI_API_KEY=your_key python scripts/generate_menu.py

# Test without intake (uses defaults)
rm data/intake.json
OPENAI_API_KEY=your_key python scripts/generate_menu.py
```

#### 3. Notion Update Script
```bash
# Test Notion integration (requires generated menu)
NOTION_TOKEN=your_token NOTION_DATABASE_ID=your_db_id python scripts/notion_update.py
```

## Dify Integration Testing

### Slack Bot Testing

#### 1. Basic Response Test
```
User: @menuplanner こんにちは
Expected: Bot responds with greeting and menu creation offer
```

#### 2. Slot Collection Test
```
User: @menuplanner 今週の献立をお願いします
Bot: どちらの週の献立を作成しますか？
User: 来週
Bot: 何日分の夕食が必要ですか？
User: 5日分
Bot: 外泊や外食の予定はありますか？
User: 土日は外食
[Continue conversation flow...]
```

#### 3. JSON Generation Test
- Verify complete conversation saves intake.json to gist
- Check JSON structure matches schema
- Validate all collected data

### Conversation Flow Validation

#### Required Slots Test
- [ ] week_start collection and Monday conversion
- [ ] days_needed validation (1-7 range)
- [ ] away_days parsing (Japanese day names)

#### Optional Slots Test  
- [ ] avoid_ingredients list parsing
- [ ] max_cooking_time validation
- [ ] cuisine_preferences selection
- [ ] memo free text handling
- [ ] guests_expected number parsing

#### Error Handling Test
- [ ] Invalid date input recovery
- [ ] Network errors during gist save
- [ ] Incomplete conversation abandonment
- [ ] Multiple concurrent users

## End-to-End Testing

### Complete Workflow Test

1. **Dify Conversation** (Friday/Saturday)
   - Start conversation in Slack
   - Complete all slot collection
   - Verify JSON saved to gist

2. **GitHub Actions Execution** (Sunday 18:00 JST)
   - Verify intake.json fetched
   - Confirm menu generation
   - Check Notion page creation

3. **Result Validation**
   - Notion page has correct content
   - Old pages are archived
   - Menu respects intake preferences

### AwayDays Functionality Test

Test the specific requirements mentioned in the issue:

#### Test Case 1: Weekend Away
```json
{
  "days_needed": 5,
  "away_days": [5, 6],  // Saturday, Sunday
  "week_start": "2024-01-15"
}
```

Expected Result:
- Monday-Friday: Generated meals
- Saturday: "外食・外泊"
- Sunday: "外食・外泊"

#### Test Case 2: Reduced Days
```json
{
  "days_needed": 3,
  "away_days": [],
  "week_start": "2024-01-15"
}
```

Expected Result:
- Monday-Wednesday: Generated meals
- Thursday-Sunday: "お休み"

#### Test Case 3: Mid-week Away
```json
{
  "days_needed": 5,
  "away_days": [2, 3],  // Wednesday, Thursday
  "week_start": "2024-01-15"
}
```

Expected Result:
- Monday, Tuesday: Generated meals
- Wednesday, Thursday: "外食・外泊"
- Friday: Generated meal
- Saturday, Sunday: "お休み"

## Performance Testing

### API Rate Limits

#### OpenAI API
- Test with multiple quick requests
- Verify rate limit handling
- Check error recovery

#### Notion API
- Test bulk page operations
- Verify pagination handling
- Check concurrent access

#### GitHub API
- Test gist fetch frequency
- Verify authentication handling
- Check network error recovery

## Security Testing

### Secrets Management
- [ ] No secrets in repository code
- [ ] GitHub Secrets properly configured
- [ ] Environment variables not logged
- [ ] Gist access permissions correct

### Data Privacy
- [ ] Personal data not logged in GitHub Actions
- [ ] Conversation logs don't contain PII
- [ ] Gist data properly secured

## Monitoring and Alerts

### GitHub Actions Monitoring
```bash
# Check recent workflow runs
gh run list --workflow="Weekly Menu Generation"

# View specific run details
gh run view <run_id>

# Check for failures
gh run list --status=failure
```

### Log Analysis
```bash
# Download workflow logs
gh run download <run_id>

# Check for common errors
grep -i error *.log
grep -i "failed" *.log
```

## Troubleshooting Common Issues

### Menu Not Generated
1. Check GitHub Actions logs
2. Verify OpenAI API key validity
3. Check intake.json format
4. Verify rules.yaml syntax

### Notion Update Failed
1. Check Notion token permissions
2. Verify database ID
3. Check database properties schema
4. Review integration access

### Dify Bot Not Responding
1. Check Slack app permissions
2. Verify Dify plugin configuration
3. Check webhook endpoints
4. Review conversation flow logic

### Intake Data Missing
1. Check gist accessibility
2. Verify GitHub token permissions
3. Review gist file naming
4. Check Dify HTTP request configuration