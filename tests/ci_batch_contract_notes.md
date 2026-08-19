CI batch root-cause notes:
- Dynamic market data explicitly marked invalid must not silently fall back to a static benchmark.
- Low-confidence dynamic market data may fall back to the static baseline with an explicit reason.
- Structured API errors should expose a stable machine-readable code and a human-readable message.
- Candidate promotion requires validated market evidence and a schema-valid Knowledge Base record.
