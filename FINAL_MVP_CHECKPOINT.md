# ToolHunterAI — Final MVP Checkpoint

The current main branch contains the integrated MVP pipeline:

- Marketplace advertisement input / Divar fetch adapter
- Advertisement normalization and validation
- Tool matching and AI-assisted discovery
- Candidate validation and promotion
- Static and dynamic market intelligence with fallback safeguards
- Risk scoring and BUY / REVIEW / DON'T BUY decision engine
- AI explanation layer
- Web result presentation
- Health endpoint and CI validation

Final acceptance gate: GitHub Actions CI must be green on the current main commit, and the supplied Divar URL must be validated through the live application before declaring production readiness.

Reference test listing supplied for final E2E validation:
https://divar.ir/v/ga8VzMlX?ref=android
