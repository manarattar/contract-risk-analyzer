param location string
param namePrefix string
param insightsId string

var queries = [
  { title: 'Requests and failure rate', query: 'requests | summarize requests=count(), failures=countif(success == false) by bin(timestamp, 1h) | extend failure_rate_pct=100.0 * failures / requests | order by timestamp asc' }
  { title: 'Pipeline latency p50 and p95', query: 'dependencies | where name startswith "pipeline." | summarize p50_ms=percentile(duration / 1ms, 50), p95_ms=percentile(duration / 1ms, 95) by name, bin(timestamp, 1h) | order by timestamp asc' }
  { title: 'LLM tokens and estimated cost per day by stage', query: 'customMetrics | where name in ("llm.tokens", "llm.cost_eur") | extend stage=tostring(customDimensions.stage), direction=tostring(customDimensions.direction) | summarize input_tokens=sumif(value, name == "llm.tokens" and direction == "input"), output_tokens=sumif(value, name == "llm.tokens" and direction == "output"), estimated_cost_eur=sumif(value, name == "llm.cost_eur") by bin(timestamp, 1d), stage | order by timestamp asc' }
  { title: '429 retries', query: 'customMetrics | where name == "llm.retries" | extend stage=tostring(customDimensions.stage) | summarize retries=sum(value) by stage, bin(timestamp, 1h) | order by timestamp asc' }
  { title: 'Exceptions', query: 'exceptions | summarize exceptions=count() by type, outerMessage, bin(timestamp, 1h) | order by timestamp desc' }
]

var items = [for (tile, i) in queries: {
  type: 3
  name: 'query-${i}'
  content: {
    version: 'KqlItem/1.0'
    query: tile.query
    size: 0
    title: tile.title
    queryType: 0
    resourceType: 'microsoft.insights/components'
  }
}]

resource workbook 'Microsoft.Insights/workbooks@2023-06-01' = {
  name: guid(insightsId, 'contract-analyzer-observability')
  location: location
  kind: 'shared'
  properties: {
    displayName: '${namePrefix} observability'
    category: 'workbook'
    sourceId: insightsId
    version: 'Notebook/1.0'
    serializedData: string({
      version: 'Notebook/1.0'
      items: items
    })
  }
}
