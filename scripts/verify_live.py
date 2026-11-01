"""Exercise a running server using only fictional samples; retain QA reports locally."""

import argparse
import json
import time
from pathlib import Path
import httpx

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--base", default="http://127.0.0.1:8080")
parser.add_argument("--kind", default="rental", choices=["rental", "freelance"])
parser.add_argument("--lang", default="en", choices=["en", "hi"])
parser.add_argument("--require-ai", action="store_true", help="Fail unless readiness and grounded local inference both work")
parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts")
args = parser.parse_args()
with httpx.Client(base_url=args.base, timeout=600, trust_env=False) as client:
    if args.require_ai:
        client.get("/api/ready").raise_for_status()
    response = client.post(
        "/api/analyze",
        files={"file": (f"sample_{args.kind}.txt", (ROOT / f"samples/sample_{args.kind}.txt").read_bytes())},
        data={"doc_type": args.kind, "lang": args.lang},
    )
    response.raise_for_status()
    sid = response.json()["session_id"]
    count = 0
    done = False
    started = time.perf_counter()
    with client.stream("GET", f"/api/analyze/{sid}/stream") as stream:
        stream.raise_for_status()
        for line in stream.iter_lines():
            if line == "event: clause_result":
                count += 1
                print(f"Clause {count} streamed at {time.perf_counter() - started:.1f}s", flush=True)
            if line == "event: error":
                raise RuntimeError("Analysis emitted an error")
            if line == "event: done":
                done = True
    result = client.get(f"/api/analyze/{sid}").json()
    flags = sum(len(c["flags"]) for c in result["clauses"])
    ai = sum(c["ai_available"] for c in result["clauses"])
    assert done and count == len(result["clauses"]), "Stream ended before all results were delivered"
    if args.require_ai:
        assert ai > 0, "No grounded local-model explanations returned"
    assert flags >= 5 and result["summary"]["overall_score"] > 0
    report = client.get(f"/api/analyze/{sid}/report.pdf")
    assert report.status_code == 200 and report.content.startswith(b"%PDF-")
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    (output / f"{args.kind}-{args.lang}-report.pdf").write_bytes(report.content)
    (output / f"{args.kind}-{args.lang}-result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    assert client.delete(f"/api/analyze/{sid}").status_code == 200
    assert client.get(f"/api/analyze/{sid}").status_code == 404
    print(
        json.dumps(
            {
                "clauses": count,
                "flags": flags,
                "grounded_ai_explanations": ai,
                "seconds": round(time.perf_counter() - started, 1),
                "pdf": "valid",
                "deletion": "verified",
            }
        ),
        flush=True,
    )
