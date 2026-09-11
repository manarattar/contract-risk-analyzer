import json,sys
from app.review.store import initialize,transaction
from app.review.pipeline import generate,answer_question,PROMPT_HASH
initialize()
blocks=[{'id':'synthetic-1','text':'The Customer shall pay all fees within 15 days. The Provider may change any fee without notice. The Provider has no liability for any loss, including loss caused by its own breach.','location':'Synthetic paragraph 1'}]
try:
 findings=generate(blocks,{'party':'Customer','role':'Customer','contract_type':'Services agreement','governing_law':'Unknown'})
 assert findings and all(f['citations'] for f in findings)
 drafts=[f for f in findings if f.get('suggested_revision')]
 assert drafts and all(f.get('revision_caveats') for f in drafts)
 answer=answer_question({'blocks':blocks},'When must the Customer pay fees?',{})
 assert answer['status']=='answered' and answer['sources']
 with transaction() as conn:reserved=conn.execute('SELECT sum(reserved_cents) FROM ai_budget').fetchone()[0]
 print(json.dumps({'passed':True,'synthetic_only':True,'finding_count':len(findings),'draft_count':len(drafts),'verified_quote_count':sum(len(f['citations']) for f in findings),'answer_quotes_verified':True,'reserved_cents':reserved,'model':'gpt-4.1-mini-2025-04-14','prompt_hash':PROMPT_HASH,'qualified_legal_evaluation':False}))
except Exception as e:
 print(json.dumps({'passed':False,'error_type':type(e).__name__,'validation_code':str(e) if str(e) in {'batch_coverage_mismatch','duplicate_finding_id','unsupported_assurance','invalid_source_span','ambiguous_source_span','incomplete_provider_output','daily_ai_budget_exhausted','unsupported_answer'} else 'see restricted operator logs','http_status':getattr(e,'status_code',None)}));sys.exit(1)
