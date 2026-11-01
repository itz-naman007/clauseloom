#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
docker compose up --build -d
docker compose exec -T app python - <<'PY'
import json, time, urllib.request
base='http://localhost:8080'
for attempt in range(120):
    try:
        urllib.request.urlopen(base+'/api/ready',timeout=5)
        break
    except Exception:
        time.sleep(2)
else:
    raise SystemExit('Model did not become ready')
boundary='clauseloom-smoke'
data=open('/app/samples/sample_rental.txt','rb').read()
body=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="sample.txt"\r\nContent-Type: text/plain\r\n\r\n'.encode()+data+f'\r\n--{boundary}--\r\n'.encode())
request=urllib.request.Request(base+'/api/analyze',data=body,headers={'Content-Type':f'multipart/form-data; boundary={boundary}'})
sid=json.load(urllib.request.urlopen(request))['session_id']
events=urllib.request.urlopen(base+f'/api/analyze/{sid}/stream',timeout=600).read().decode()
assert 'event: done' in events, events[-300:]
result=json.load(urllib.request.urlopen(base+f'/api/analyze/{sid}'))
assert sum(len(c['flags']) for c in result['clauses'])>=5
assert any(c['ai_available'] for c in result['clauses']), 'No grounded local-model explanations returned'
assert urllib.request.urlopen(base+f'/api/analyze/{sid}/report.pdf').read().startswith(b'%PDF-')
urllib.request.urlopen(urllib.request.Request(base+f'/api/analyze/{sid}',method='DELETE'))
print('PASS: local model, streaming, flags, PDF and deletion')
PY
