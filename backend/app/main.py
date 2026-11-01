import asyncio
import json
import logging
import re
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException
from fastapi.responses import JSONResponse, Response, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse
from .config import settings
from .core.session import store
from .core.pipeline import analyze
from .llm.client import model
from .report.pdf import make_report
from .core.body_limit import BodyLimit

ROOT = Path(__file__).resolve().parents[2]
SAMPLES = ROOT / "samples"
if not SAMPLES.exists():
    SAMPLES = ROOT.parent / "samples"
logger = logging.getLogger("clauseloom")
logging.basicConfig(level=logging.INFO, format="%(message)s")
limits = defaultdict(deque)


@asynccontextmanager
async def lifespan(app):
    async def cleanup():
        while True:
            await asyncio.sleep(15)
            store.purge()
            now = time.monotonic()
            for ip in list(limits):
                if not limits[ip] or now - limits[ip][-1] > 3600:
                    del limits[ip]

    cleaner = asyncio.create_task(cleanup())
    warmer = asyncio.create_task(model.warm())
    yield
    cleaner.cancel()
    warmer.cancel()
    tasks = [s.task for s in store.sessions.values() if s.task]
    for sid in list(store.sessions):
        store.delete(sid)
    await asyncio.gather(cleaner, warmer, *tasks, return_exceptions=True)


app = FastAPI(title="ClauseLoom", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.origins),
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Last-Event-ID"],
)


app.add_middleware(BodyLimit)


@app.middleware("http")
async def security(request: Request, call_next):
    start = time.perf_counter()
    # Reject cross-site mutations, including multipart form submissions.
    origin = request.headers.get("origin")
    if (
        request.method in {"POST", "DELETE"}
        and origin
        and origin not in settings.origins
        and origin != str(request.base_url).rstrip("/")
    ):
        return JSONResponse({"detail": "This origin is not allowed."}, status_code=403)
    response = await call_next(request)
    response.headers.update(
        {
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer",
            "Cache-Control": "no-store",
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self' data:; connect-src 'self'; "
            f"frame-ancestors {settings.frame_ancestors}; base-uri 'none'; form-action 'self'",
            "Permissions-Policy": "camera=(self), microphone=(), geolocation=()",
        }
    )
    logger.info(
        json.dumps(
            {
                "event": "request",
                "method": request.method,
                "status": response.status_code,
                "ms": round((time.perf_counter() - start) * 1000),
            }
        )
    )
    return response


@app.exception_handler(Exception)
async def error_handler(request, exc):
    return JSONResponse({"detail": "Something went wrong. Please try again."}, status_code=500)


def get_session(sid):
    session = store.get(sid)
    if not session:
        raise HTTPException(404, "This session was deleted or expired. Please analyze the document again.")
    return session


@app.post("/api/analyze")
async def upload(
    request: Request,
    file: UploadFile = File(...),
    doc_type: Literal["auto", "rental", "freelance"] = Form("auto"),
    lang: Literal["en", "hi"] = Form("en"),
    redact_pii: bool = Form(False),
):
    ip = request.client.host if request.client else "local"
    now = time.monotonic()
    bucket = limits[ip]
    while bucket and now - bucket[0] > 3600:
        bucket.popleft()
    if len(bucket) >= settings.rate_limit or len(limits) > 10000:
        raise HTTPException(429, "Please wait before starting another analysis.")
    bucket.append(now)
    try:
        data = await file.read(settings.max_upload + 1)
    finally:
        await file.close()
    if not data or len(data) > settings.max_upload:
        raise HTTPException(413, f"Please choose a non-empty file under {settings.max_upload // 1024 // 1024} MB.")
    filename = re.sub(r"[^\w. -]", "_", (file.filename or "document.txt").replace("\\", "/").split("/")[-1])[:100]
    try:
        session = store.create(len(data))
    except ValueError as exc:
        raise HTTPException(503, str(exc)) from None
    session.task = asyncio.create_task(analyze(session, data, filename, doc_type, lang, redact_pii))
    return {"session_id": session.id}


@app.get("/api/analyze/{sid}/stream")
async def stream(sid: str, request: Request):
    session = get_session(sid)
    try:
        cursor = max(0, min(int(request.headers.get("last-event-id", "0")), len(session.events)))
    except ValueError:
        cursor = 0

    async def events():
        nonlocal cursor
        while not session.deleted:
            while cursor < len(session.events):
                event = session.events[cursor]
                cursor += 1
                yield event
            if session.done or await request.is_disconnected():
                break
            session.changed.clear()
            try:
                await asyncio.wait_for(session.changed.wait(), timeout=10)
            except asyncio.TimeoutError:
                yield {
                    "event": "status",
                    "data": json.dumps({"stage": "waiting", "notice": "The local model may take 1–3 minutes on a CPU."}),
                }
        if session.deleted:
            yield {"event": "error", "data": json.dumps({"message": "Session deleted or expired."})}

    return EventSourceResponse(events(), ping=10, headers={"X-Accel-Buffering": "no"})


@app.get("/api/analyze/{sid}")
async def result(sid: str):
    session = get_session(sid)
    if not session.done:
        return JSONResponse({"status": "processing"}, status_code=202)
    if session.result.get("summary") is None:
        raise HTTPException(422, "Analysis did not finish. Please try another file.")
    return session.result


@app.delete("/api/analyze/{sid}")
async def delete(sid: str):
    get_session(sid)
    store.delete(sid)
    return {"deleted": True}


@app.get("/api/analyze/{sid}/report.pdf")
async def report(sid: str):
    session = get_session(sid)
    if not session.done or not session.result.get("summary"):
        raise HTTPException(409, "Please wait for analysis to finish.")
    content = await asyncio.to_thread(make_report, session.result)
    return Response(
        content, media_type="application/pdf", headers={"Content-Disposition": 'attachment; filename="clauseloom-report.pdf"'}
    )


@app.get("/api/sample/{kind}")
async def sample(kind: Literal["rental", "freelance"]):
    return FileResponse(SAMPLES / f"sample_{kind}.txt", media_type="text/plain", filename=f"sample_{kind}.txt")


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "model": settings.model,
        "model_loaded": model.loaded and model.inference_ready,
        "warming": model.warming,
        "session_ttl_min": settings.ttl // 60,
        "max_upload_mb": settings.max_upload // 1024 // 1024,
    }


@app.get("/api/ready")
async def ready():
    available = await model.available()
    available = available and model.inference_ready
    return JSONResponse(
        {"status": "ready" if available else "degraded", "model": settings.model, "model_loaded": available},
        status_code=200 if available else 503,
    )


static = Path(__file__).parent / "static"
if static.exists():
    app.mount("/", StaticFiles(directory=static, html=True), name="frontend")
