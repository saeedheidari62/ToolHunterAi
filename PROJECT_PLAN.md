# ToolHunterAI Project Plan

## Vision
Build the most trusted AI-powered marketplace assistant for buying and selling used industrial power tools.

## Mission
Help buyers make safer decisions by analysing listings, estimating risk, and reducing fraud.

## Current Milestone
MVP implementation is complete; the project is in the final production-readiness gate.

### Working architecture
- Divar fetch and normalization
- Advertisement collection and metadata preservation
- Tool matching and variant matching
- Market-price intelligence with city-aware search and outlier filtering
- Technical intelligence normalization
- Candidate discovery / validation / promotion
- Unified evidence layer
- Knowledge Base schema validation
- Decision engine and ranking
- History / API / web application layers
- AI explanation layer
- Production Render deployment configuration
- GitHub Actions regression workflow

### Final acceptance gate
1. GitHub Actions CI is green on the current main commit.
2. Production deployment is reachable and `/health` responds successfully.
3. The reference Divar listing is successfully processed through the live production pipeline.
4. The returned result contains tool identification, market/risk analysis, decision, and AI explanation.

### Revenue MVP — immediately after acceptance
- Freeze the MVP architecture.
- Expose the buyer workflow as the primary product path.
- Measure real listing analyses, successful analyses, BUY/REVIEW/DON'T BUY distribution, and repeat usage.
- Add only revenue-critical functionality; no opportunistic architecture changes.

## Founders
- Saeed Heidari

## Technical Partner
- ChatGPT (AI Assistant)
