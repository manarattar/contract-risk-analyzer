import json
import os
import subprocess
import sys
import pytest
from app.review.sandbox import environment

@pytest.mark.skipif(sys.platform!='linux', reason='Linux kernel isolation requires Linux')
def test_sandbox_denies_other_files_writes_sockets_and_processes(tmp_path):
    allowed=tmp_path/'input.txt';allowed.write_text('synthetic input')
    foreign=tmp_path/'private.txt';foreign.write_text('other account')
    script='''
import json,os,socket,subprocess,sys
from pathlib import Path
from app.review.sandbox import restrict
restrict(sys.argv[1])
assert Path(sys.argv[1]).read_text()=='synthetic input'
checks=[]
for operation in [lambda:Path(sys.argv[2]).read_text(),lambda:Path(sys.argv[1]).write_text('changed'),lambda:socket.socket(),lambda:subprocess.run(['/bin/true']),lambda:Path('/proc/self/environ').read_bytes()]:
 try:operation()
 except (PermissionError,OSError):checks.append(True)
 else:checks.append(False)
print(json.dumps(checks))
'''
    result=subprocess.run([sys.executable,'-B','-c',script,str(allowed),str(foreign)],capture_output=True,text=True,env=environment(True))
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout)==[True]*5
    assert allowed.read_text()=='synthetic input'

def test_parser_environment_excludes_secrets(monkeypatch):
    monkeypatch.setenv('REVIEW_API_KEY','synthetic-secret')
    assert 'REVIEW_API_KEY' not in environment(True)
    assert 'REVIEW_PRINCIPALS_JSON' not in environment(True)


@pytest.mark.skipif(sys.platform!='linux', reason='Linux kernel isolation requires Linux')
def test_pdf_parse_and_render_with_restrictions(tmp_path):
    import hashlib
    from app.review.sample import pdf_bytes
    source=tmp_path/'synthetic.pdf';source.write_bytes(pdf_bytes())
    result=subprocess.run([sys.executable,'-B','-m','app.review.parser',str(source),'pdf','50','150000'],capture_output=True,text=True,env=environment(True))
    assert result.returncode==0,result.stdout+result.stderr
    parsed=json.loads(result.stdout)
    assert parsed['page_count']==2
    result=subprocess.run([sys.executable,'-B','-m','app.review.page_renderer'],input=json.dumps({'path':str(source),'hash':hashlib.sha256(source.read_bytes()).hexdigest(),'page':1,'block':None,'quote':'','page_blocks':[]}),capture_output=True,text=True,env=environment(True))
    assert result.returncode==0,result.stdout+result.stderr
    assert 'image' in result.stdout
