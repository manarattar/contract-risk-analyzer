# Evaluation suite

The suite measures clause risk precision, recall and level accuracy, missing-clause recall, retrieval hit rate at k, answer keywords, judge groundedness, and overall-score stability. It calls backend services directly; it does not use the HTTP API or Postgres.

From `backend/`, install `requirements.txt` and set `PYTHONPATH=.`. For Azure, run `az login` and set `LLM_PROVIDER=azure_openai`, `VECTOR_BACKEND=azure_search`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_CHAT_DEPLOYMENT`, `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`, and `AZURE_SEARCH_ENDPOINT`. DefaultAzureCredential uses the Azure login. Alternatively, set `OPENAI_API_KEY` for the OpenAI provider and use the default Chroma vector store. Run `python -m evals.run`; use `--contracts bad good`, `--k`, `--stability-runs`, `--out`, `--thresholds`, or `--no-fail` as needed.

A full run makes many model and embedding calls and can take several minutes and incur cost. The Azure deployment has a 10K TPM quota; the backend retries rate limits with a 65-second backoff. Thresholds in `thresholds.json` are regression floors set just below the 2026-10-08 baseline (`docs/evals-baseline.md`). Raise them when the analyzer improves; never lower them to make a run pass without recording why.
