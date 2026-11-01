"""Inspect model behavior on a fixed fictional clause (never user data)."""
import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.llm.client import LocalModel, PROMPTS
from app.models import Explanation

async def main():
    client=LocalModel()
    source='The client may request unlimited revisions.'
    for lang in ['en','hi']:
        system=(PROMPTS/'system.txt').read_text(encoding='utf-8')
        system+='\nRespond in simple Hindi in Devanagari. Keep evidence_quote in original English.' if lang=='hi' else '\nRespond in English.'
        raw=await client.request(system,f'<clause>{source}</clause>',Explanation.model_json_schema())
        print(json.dumps({'lang':lang,'output':json.loads(raw)},ensure_ascii=True),flush=True)
asyncio.run(main())
