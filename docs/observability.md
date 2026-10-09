# Observability

Set `APPLICATIONINSIGHTS_CONNECTION_STRING` to enable Azure Monitor export. Without it, the app starts and serves `/api/health` without configuring any exporter. The service name is `contract-analyzer-backend`; health requests are excluded from FastAPI tracing.

## Trace tree

```text
POST /api/upload
  pipeline.upload
    pipeline.parse
    pipeline.split
    pipeline.analyse
      pipeline.analyse.detect ? llm.chat (stage=detect)
      pipeline.analyse.clauses ? llm.chat (stage=clauses)
      pipeline.analyse.missing ? llm.chat (stage=missing)
      pipeline.analyse.contradictions ? llm.chat (stage=contradictions)
      pipeline.analyse.score
    pipeline.embed_index ? llm.embed (stage=index)
POST /api/qa
  pipeline.qa
    pipeline.qa.search ? llm.embed (stage=qa, Azure Search)
    pipeline.qa.answer ? llm.chat (stage=qa)
```

Spans carry document ID, file type, clause count, batch size, score, risk level, and vector backend where relevant. Exceptions are recorded even when a fallback handles them. Prompts and contract text are not attached to telemetry.

## Metrics

`llm.latency_ms` is a histogram. `llm.tokens` is a counter with `direction` (`input` or `output`), `model`, and `stage`. `llm.retries` counts 429 attempts. `llm.cost_eur` is an estimated EUR counter. Prices in `app/config.py` are configurable per million tokens for `gpt-5-mini` input/output and `text-embedding-3-small` input. They are estimates; check current provider billing rates before treating them as spend.

## Workbook queries

Open Azure Portal ? Application Insights ? `contract-analyzer-insights` ? Workbooks ? `contract-analyzer observability`. The same queries can be pasted into Application Insights ? Logs.

### Requests and failure rate

```kusto
requests | summarize requests=count(), failures=countif(success == false) by bin(timestamp, 1h) | extend failure_rate_pct=100.0 * failures / requests | order by timestamp asc
```

### Pipeline latency

```kusto
dependencies | where name startswith "pipeline." | summarize p50_ms=percentile(duration / 1ms, 50), p95_ms=percentile(duration / 1ms, 95) by name, bin(timestamp, 1h) | order by timestamp asc
```

### Tokens and estimated cost per day by stage

```kusto
customMetrics | where name in ("llm.tokens", "llm.cost_eur") | extend stage=tostring(customDimensions.stage), direction=tostring(customDimensions.direction) | summarize input_tokens=sumif(value, name == "llm.tokens" and direction == "input"), output_tokens=sumif(value, name == "llm.tokens" and direction == "output"), estimated_cost_eur=sumif(value, name == "llm.cost_eur") by bin(timestamp, 1d), stage | order by timestamp asc
```

### 429 retries

```kusto
customMetrics | where name == "llm.retries" | extend stage=tostring(customDimensions.stage) | summarize retries=sum(value) by stage, bin(timestamp, 1h) | order by timestamp asc
```

### Exceptions

```kusto
exceptions | summarize exceptions=count() by type, outerMessage, bin(timestamp, 1h) | order by timestamp desc
```
