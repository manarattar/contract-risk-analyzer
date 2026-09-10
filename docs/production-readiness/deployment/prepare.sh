#!/bin/sh
set -eu
release="$1"
case "$release" in review-[0-9]*-[0-9]*) ;; *) exit 2 ;; esac
case "$release" in *[!a-z0-9-]*) exit 2 ;; esac
root="/srv/apps/contracts-v2/releases/$release"
cd "$root"
tar xzf backend-release.tar.gz
printf 'RELEASE_ID=%s\n' "$release" > .env
sudo -n python3 - <<'PY'
import hashlib,json,os,secrets
from pathlib import Path
root=Path('/srv/stack/env')
path=root/'contracts-v2.env'
if not path.exists():
    token=secrets.token_urlsafe(48)
    principal=[{'id':'manar','workspace_id':'private-manar','role':'owner','token_sha256':hashlib.sha256(token.encode()).hexdigest()}]
    values={
      'REVIEW_MODE':'manual','REVIEW_DATA_DIR':'/app/data/review-v2',
      'REVIEW_UPLOAD_ENABLED':'false','REVIEW_PAGE_RENDERING_ENABLED':'false',
      'REVIEW_PARSER_ISOLATION_APPROVED':'false','REVIEW_PUBLIC_DEMO_ENABLED':'true',
      'REVIEW_DEMO_SIGNING_KEY':secrets.token_urlsafe(48),
      'REVIEW_PRINCIPALS_JSON':"'"+json.dumps(principal)+"'",
      'REVIEW_ALLOWED_ORIGINS':'https://contracts.manarattar.com',
      'REVIEW_PROVIDER_NAME':'No provider enabled',
      'REVIEW_PRIVACY_DESCRIPTION':'Private uploads are disabled. Public examples are synthetic and isolated for 30 minutes.',
      'REVIEW_PROVIDER_RETENTION':'No provider calls are enabled.',
      'REVIEW_BACKUP_RETENTION':'Backup policy is pending verification; no confidential uploads are accepted.'}
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as f: f.write('\n'.join(k+'='+v for k,v in values.items())+'\n')
    fd=os.open(root/'contracts-v2-owner-token',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as f: f.write(token+'\n')
print('Protected v2 configuration available; credentials not printed.')
PY
sudo -n docker build -t "contracts-review-v2:$release" backend
sudo -n docker compose --profile setup run --rm initialize
sudo -n docker compose up -d api worker
sudo -n docker compose ps
