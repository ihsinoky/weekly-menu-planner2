# Title: Evaluation of Weekly Menu Planning Implementation Options: Baseline vs Dify Integration

- **Date**: 2025 - 09 - 14 (Asia/Tokyo)
- **Status**: Proposed (Under discussion)

## Context

**Existing system**: The weekly menu planning service currently relies on GitHub Actions triggered by a cron schedule (JST Sunday 18:00), a Python script that reads `rules.yaml`, generates a menu via the OpenAI API, and writes the result to a Notion database. User input for special circumstances (e.g., number of days, away days) is collected via a Notion intake database or Slack forms. The system ensures one weekly page per week by archiving previous pages and re creating them.

**Motivation for change**: The user wants a more conversational interface for specifying weekly constraints (for example, “I’m visiting family; only need 3 days of meals”). Slack is the preferred communication channel. Dify, an open source LLM workflow tool, provides Slack plug‟ins that can mediate conversation with a Chatflow/agent and optionally post responses back to Slack【807365913088259†screenshot】. Dify Slack‟bot examples show that the bot listens to Slack events (mentions or reaction triggers) and forwards them to a configured Dify app that posts the result back to Slack threads【807365913088259†screenshot】. Another article demonstrates building a Slack bot with Dify that listens to natural language questions, forwards them to a Dify AI backend (using a knowledge base and LLM), and posts answers back into Slack【407435304793699†screenshot】. This suggests Dify could handle multi‟turn conversations for menu planning.

Three options are considered:

1. **Baseline (existing design)**: Slack intake via Notion forms or Slack forms, Python and GitHub Actions for menu generation and Notion update. No Dify.
2. **D 1**: Use Dify solely for the Slack conversational intake. Dify collects user preferences through multi‟turn conversation and posts a JSON intake file to a repository or storage. The existing Python/GitHub Actions pipeline reads this file along with `rules.yaml`, generates the weekly menu, and writes to Notion. Generation and Notion writing remain outside Dify.
3. **D 2**: Use Dify for both intake and menu generation. After collecting user input, a Dify workflow calls the LLM to generate the menu and uses the HTTP request tool to write the result to Notion. GitHub Actions would only trigger the Dify workflow or might not be required if the workflow is manually triggered via Slack.

## Options and Comparison

| Option | Intake method | Generation/Notion integration | Cost | Pros (keywords) | Cons (keywords) |
|-------|---------------|-------------------------------|-----|-----------------|-----------------|
| **Baseline** | Notion intake DB or Slack forms; simple forms; minimal conversation | Python script via GitHub Actions updates Notion DB; stable | Minimal cost (uses existing Pro plans); self‟hosted control | Mature pipeline; testable; GitHub Actions free; clear version control | Intake is not conversational; user must fill forms; integration complexity when adding multi‟turn conversation; modifications require code changes |
| **D 1 (Dify as intake only)** | Dify Slack bot collects preferences via conversational flow; posts JSON to storage | GitHub Actions + Python generate menu and update Notion | Dify free tier may suffice; minimal extra cost; uses existing GitHub Actions | Conversational intake through Slack; can handle multi‟turn questions; unaffected generation pipeline; easier to maintain LLM prompts | Additional service dependency; two systems (Dify for intake and GitHub for generation); Dify must save JSON externally; potential latency |
| **D 2 (Dify end‟to‟end)** | Dify Slack bot collects preferences via conversation | Dify workflow calls LLM to generate menu and uses HTTP tool to post to Notion; may need scheduled trigger | Dify usage may incur cost depending on usage; no need for GitHub Actions | Single system; conversation and generation integrated; Slack responses can include final menu; easier to adjust conversation in Dify UI | Higher dependency on Dify; limited control over error handling; Notion API calls and archival logic must be implemented via Dify; versioning and testing harder; vendor lock‟in |

## Decision

At this stage, **Option D‟1** is recommended for the conversational intake requirement. It leverages Dify’s Slack plug‟ins to collect user preferences through a multi‟turn dialogue while preserving the stability and control of the existing GitHub Actions–Python–Notion pipeline. This hybrid approach offers the best balance between improved user experience and maintainability.

## Rationale

1. **Conversation capability**: Dify’s Slack plug‟ins support receiving messages and posting results back into Slack threads【807365913088259†screenshot】, and examples show how to forward natural‟language queries to a Dify backend and respond【407435304793699†screenshot】. Therefore, Dify can handle conversational intake.
2. **Maintainability**: Keeping the generation logic in Python and GitHub Actions retains the existing test infrastructure and allows fine‟grained control over error handling, schema validation, and Notion integration. Option D‟2 would require implementing archival logic and Notion API calls inside Dify’s workflow tool, which may be less flexible.
3. **Cost and reliability**: Option D‟1 incurs little additional cost; Dify’s free tier can be sufficient for a single user’s intake conversation. Option D‟2 would increase dependency on Dify; any changes to Dify’s API or pricing could break the pipeline.
4. **Extensibility**: With Option D‟1, we can continue to enhance the Python script (e.g., inventory integration, nutrient analysis) without being constrained by Dify’s tool capabilities. Option D‟2 could limit such enhancements.

## Consequences

- A new Dify workflow and Slack bot must be created to handle the multi‟turn conversation and produce a JSON file. Implementation will require state management and schema validation inside Dify.
- The GitHub Actions pipeline will need to fetch the JSON intake (e.g., from a repository or storage) and merge it with `rules.yaml`.
- Monitoring across two systems is required (Dify for intake and GitHub Actions for generation).
- The baseline forms‟based intake remains as a fallback in case Dify fails or the user does not interact with the Slack bot.

## Future Considerations

- Evaluate Dify’s pricing and long‟term viability; switch to baseline intake if necessary.
- Investigate Dify’s support for scheduled workflows; D‟2 could become more attractive if Dify introduces robust scheduling and better integration features.
- Consider implementing a fallback conversation flow within GitHub (e.g., using issue forms) to avoid dependency on Dify.
