# Demo Script

A step-by-step walkthrough for portfolio demos and interviews.

## Setup (30 seconds)

1. Start backend: `cd backend && uvicorn app.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Open http://localhost:5173

> No API key? Leave `.env` empty — mock mode activates automatically.

## Demo Flow

### Step 1: Show the landing page (10 seconds)
- Point out the clean drag-and-drop interface
- Mention the prominent disclaimer — "this is a professional tool, not a toy"

### Step 2: Upload the sample contract (15 seconds)
- Drag `backend/sample_contract.txt` onto the upload zone
- Watch the upload progress, then the spinner with "Analyzing clauses..."
- Explain: "It's running clause extraction and LLM analysis in the background"

### Step 3: Walk through the results (60 seconds)
- **Risk Score gauge** — "Overall score of 68/100, Medium risk. The gauge animates in."
- **Document Summary** — "AI-written summary of what this contract is about"
- **Main Risks panel** — "5 key risk factors identified, plain English"
- **Missing Clauses** — "Flags that Data Protection and Dispute Resolution are absent — which is a real red flag"

### Step 4: Explore the clause table (30 seconds)
- Click the "Score" column header to sort — show High risk clauses rising to top
- Click the "Limitation of Liability" row
- Slide-out drawer shows: original text, risk explanation, suggested revision, negotiation advice
- "Each clause has 8 structured fields returned by the LLM"

### Step 5: Contract Q&A (30 seconds)
- Type: "What are the payment terms?"
- Show the answer appear
- Type: "Can the vendor terminate without cause?"
- Explain: "It uses vector search over the contract text, then LLM to synthesize the answer"

### Step 6: Download PDF Report (15 seconds)
- Click "Download PDF Report"
- Open the downloaded file — show the risk-colored table, clause details, disclaimer footer
- "This is portfolio-quality output — something you could hand to a client"

## Talking Points for Interviews

- "I built a full async processing pipeline — upload triggers a background task, frontend polls for status, results are streamed back"
- "Mock mode means this always works in a demo, even without an API key or credits"
- "The vector store gives it semantic understanding of the contract for Q&A, not just keyword search"
- "I made it OpenAI-compatible so it works with Groq, Ollama, or any other provider — just change the base URL"
- "The risk analyzer returns strict Pydantic-validated JSON — no hallucinated fields, no schema drift"
