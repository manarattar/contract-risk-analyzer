import json
from types import SimpleNamespace
import pytest
from .test_review_v2 import client
from app.review import pipeline
from app.review.store import transaction


def test_provider_budget_stops_before_network(client,monkeypatch):
    calls=[]
    cfg=SimpleNamespace(mode='trial',daily_ai_budget_cents=20,api_key='synthetic',api_base_url='https://api.openai.com/v1',model='gpt-4.1-mini-2025-04-14')
    monkeypatch.setattr(pipeline,'settings',lambda:cfg)
    class Fake:
        def __init__(self,**kwargs):self.chat=SimpleNamespace(completions=self)
        def create(self,**kwargs):
            calls.append(kwargs)
            assert kwargs['store'] is False
            return SimpleNamespace(choices=[SimpleNamespace(finish_reason='stop',message=SimpleNamespace(content='{}'))])
    import openai
    monkeypatch.setattr(openai,'OpenAI',Fake)
    pipeline.provider_json('Synthetic',{'text':'one'})
    pipeline.provider_json('Synthetic',{'text':'two'})
    with pytest.raises(ValueError,match='daily_ai_budget_exhausted'):pipeline.provider_json('Synthetic',{'text':'three'})
    assert len(calls)==2
    with transaction() as conn:assert conn.execute('SELECT reserved_cents FROM ai_budget').fetchone()[0]==20


def test_ai_answers_reject_fabricated_evidence(monkeypatch):
    source={'blocks':[{'id':'b1','text':'Payment is due within thirty days.','location':'Paragraph 1'}]}
    monkeypatch.setattr(pipeline,'settings',lambda:SimpleNamespace(model='synthetic'))
    monkeypatch.setattr(pipeline,'provider_json',lambda *a:{'answer':'Payment is due in thirty days.','citations':[{'block_id':'b1','quote':'Payment is due within thirty days.'}]})
    answer=pipeline.answer_question(source,'When is payment due?',{})
    assert answer['status']=='answered' and answer['sources'][0]['start']==0
    monkeypatch.setattr(pipeline,'provider_json',lambda *a:{'answer':'Payment is due tomorrow.','citations':[{'block_id':'b1','quote':'tomorrow'}]})
    with pytest.raises(ValueError,match='invalid_source_span'):pipeline.answer_question(source,'When is payment due?',{})
    monkeypatch.setattr(pipeline,'provider_json',lambda *a:{'answer':'It is safe to sign.','citations':[]})
    with pytest.raises(ValueError,match='unsupported_answer'):pipeline.answer_question(source,'When is payment due?',{})
    assert pipeline.answer_question(source,'What about zebras?',{})['status']=='abstained'


def test_reflowed_quote_maps_to_original_text():
    blocks=[{'id':'b1','text':'Payment is due\nwithin thirty days.','location':'Page 1'}]
    raw={'block_ids':['b1'],'findings':[{'id':'f1','title':'Payment','explanation':'Check deadline.','uncertainty':'Review needed.','action':'Check source.','citations':[{'block_id':'b1','quote':'Payment is due within thirty days.'}]}]}
    result=pipeline.validate_generated(raw,blocks)
    assert result[0]['citations'][0]['quote']==blocks[0]['text']
    assert result[0]['citations'][0]['end']==len(blocks[0]['text'])
