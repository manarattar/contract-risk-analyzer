"""Switch only this hostname after staging passes; preserve a scoped rollback."""
import re
from pathlib import Path
import subprocess
import sys

release = sys.argv[1]
if not re.fullmatch(r'review-\d{8}-\d{6}', release):
    raise SystemExit('Invalid release identifier')
root = Path('/srv/apps/contracts-v2/releases') / release
web = Path('/srv/www/contracts-v2') / release
if not (web / 'index.html').is_file():
    raise SystemExit('Frontend release is missing')
subprocess.run(['curl','--fail','--silent','http://127.0.0.1:18800/api/ready'],check=True)
path = Path('/srv/stack/Caddyfile')
before = path.read_text()
pattern = r'^contracts\.manarattar\.com \{\n.*?^\}'
matches = list(re.finditer(pattern,before,re.M|re.S))
if len(matches) != 1:
    raise SystemExit('Expected exactly one existing hostname block')
previous = matches[0].group()
backup = root / 'previous-host-block.Caddyfile'
if not backup.exists():
    backup.write_text(previous)
replacement = '''contracts.manarattar.com {
    encode gzip zstd
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Content-Type-Options "nosniff"
        Referrer-Policy "no-referrer"
        X-Frame-Options "DENY"
        Cache-Control "no-store"
        Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
        Permissions-Policy "geolocation=(), camera=(), microphone=(), payment=(), usb=()"
        -Server
    }
    request_body {
        max_size 11MB
    }
    respond /robots.txt "User-agent: *\\nDisallow: /\\n"
    respond /sitemap.xml 404
    respond /llms.txt "Synthetic contract review demo. Private reviews require sign-in. No legal advice."
    handle /api/* {
        reverse_proxy contracts-v2:8000
    }
    handle {
        root * WEBROOT
        try_files {path} /index.html
        file_server
    }
}'''.replace('WEBROOT',str(web))
updated = before[:matches[0].start()] + replacement + before[matches[0].end():]
if path.read_text() != before:
    raise SystemExit('Shared Caddy configuration changed; inspect before retrying')
path.write_text(updated)
try:
    subprocess.run(['docker','exec','caddy','caddy','validate','--config','/etc/caddy/Caddyfile','--adapter','caddyfile'],check=True)
    subprocess.run(['docker','exec','caddy','caddy','reload','--config','/etc/caddy/Caddyfile','--adapter','caddyfile'],check=True)
except Exception:
    # Restore only our hostname if another operator changed other blocks meanwhile.
    current = path.read_text()
    if replacement in current:
        path.write_text(current.replace(replacement,previous,1))
    raise
print('Hostname switched to '+release+'. Previous hostname block preserved.')
