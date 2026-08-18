# ToolHunterAI Project Plan

## Vision
Build the most trusted AI-powered marketplace assistant for buying and selling used industrial power tools.

## Mission
Help buyers make safer decisions by analysing listings, estimating risk, and reducing fraud.

## Current Milestone
Core MVP pipeline is implemented and under regression hardening.

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
- GitHub Actions regression workflow

### Current blocker
- OpenAI API Secret is not configured in the development environment, so AI enrichment/discovery paths must remain optional and fail safely.

### Immediate priorities
1. Keep the single `backend.api` production pipeline as the source of truth.
2. Maintain regression coverage for every cross-layer contract.
3. Harden Market Intelligence, Variant Intelligence, Knowledge Base persistence, and Promotion concurrency.
4. Verify GitHub Actions health after repository changes.
5. Activate AI enrichment only after `OPENAI_API_KEY` is available.

## Founders
- Saeed Heidari

## Technical Partner
- ChatGPT (AI Assistant)
