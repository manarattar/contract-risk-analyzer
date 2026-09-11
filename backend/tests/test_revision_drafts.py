import pytest
from .test_review_v2 import client,processed,auth
from app.review.pipeline import validate_generated


def test_revision_requires_caveats_and_rejects_assurances():
    blocks=[{'id':'b1','text':'Fees are payable within fifteen days.','location':'Paragraph 1'}]
    finding={'id':'f1','title':'Payment timing','explanation':'Check timing.','uncertainty':'Business preference unknown.','action':'Discuss timing.','citations':[{'block_id':'b1','quote':blocks[0]['text']}],'suggested_revision':'Fees are payable within [agreed period].'}
    raw={'block_ids':['b1'],'findings':[finding]}
    with pytest.raises(ValueError,match='revision_caveats_missing'):validate_generated(raw,blocks)
    finding['revision_caveats']='Confirm period with the reviewer.'
    assert validate_generated(raw,blocks)[0]['suggested_revision']==finding['suggested_revision']
    finding['suggested_revision']='This contract is safe to sign.'
    with pytest.raises(ValueError,match='unsupported_assurance'):validate_generated(raw,blocks)


def test_saved_revision_export_escapes_text_and_preserves_source(client):
    identifier,document=processed(client)
    finding=document['result']['findings'][0]
    assert finding['suggested_revision'] and finding['revision_caveats']
    before=client.get(f'/api/v2/documents/{identifier}/source',headers=auth()).json()
    draft='<script>alert("synthetic")</script> proposed wording'
    response=client.patch(f'/api/v2/documents/{identifier}/findings/'+finding['id'],headers=auth(),json={'status':'edited','note':'Synthetic reviewer changed the wording.','revision_text':draft,'version':0})
    assert response.status_code==200,response.text
    export=client.get(f'/api/v2/documents/{identifier}/export',headers=auth()).text
    assert 'Illustrative suggested wording (not approved)' in export
    assert '&lt;script&gt;' in export and '<script>' not in export
    assert client.get(f'/api/v2/documents/{identifier}/source',headers=auth()).json()==before
