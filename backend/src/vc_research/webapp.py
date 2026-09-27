"""Single-process, loopback-only demo server. No work occurs on startup or GET."""
from pathlib import Path
from threading import Lock

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .demo.config import readiness
from .demo.finance import ReviewRequest, calculate
from .demo.live import LiveProvider, RunError
from .demo.models import AnalyzeRequest
from .demo.offline import OfflineProvider
from .demo.pipeline import run_analysis, memo_markdown
from .sourcing.core import DiscoverRequest, LiveDiscovery, discover
from .sourcing.offline import OfflineDiscovery

STATIC = Path(__file__).parent / "demo" / "static"
app = FastAPI(title="VC Analyst AI — local demo", docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"])
app.state.lock = Lock()
app.state.report = None


@app.middleware("http")
async def local_boundary(request: Request, call_next):
    if request.method not in {"GET", "HEAD"}:
        origin = request.headers.get("origin")
        if request.headers.get("x-vc-client") != "local-browser" or (origin and origin != str(request.base_url).rstrip("/")):
            return JSONResponse({"detail": "Only same-origin local browser requests are accepted."}, status_code=403)
        # Bound decoded payload before validation; never log company inputs or request bodies.
        size, chunks = 0, []
        async for part in request.stream():
            size += len(part)
            if size > 4096:
                return JSONResponse({"detail": "Request is too large."}, status_code=413)
            chunks.append(part)
        request._body = b"".join(chunks)  # Replay this bounded body to FastAPI's validator.
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    return response


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/status")
def status():
    return {**readiness(), "busy": app.state.lock.locked()}


@app.post("/api/analyze")
def analyze(request: AnalyzeRequest):
    if request.mode == "live" and not request.confirm_live:
        raise HTTPException(403, "Confirm the bounded live run in the browser first.")
    if not app.state.lock.acquire(blocking=False):
        raise HTTPException(409, "An operation is already running. No new request was sent.")
    provider = None
    try:
        provider = LiveProvider() if request.mode == "live" else OfflineProvider(request.company)
        report = run_analysis(request.company.strip(), provider, request.mode)
        app.state.report = report  # Only the last successful result; never cache live searches.
        return report
    except RunError as exc:
        return JSONResponse({"detail": str(exc), "usage": provider.usage() if provider else None}, status_code=422)
    except Exception:
        # No provider content, credentials or traceback in the UI; no automatic retry.
        return JSONResponse({"detail": "The run failed validation or received an unexpected provider response. No retry was attempted. Previous successful results remain available.",
                             "usage": provider.usage() if provider else None}, status_code=502)
    finally:
        app.state.lock.release()


@app.post("/api/financials")
def financials(request: ReviewRequest):
    if not app.state.lock.acquire(blocking=False):
        raise HTTPException(409, "An operation is already running.")
    try:
        report = app.state.report
        if not report or report["run_id"] != request.run_id:
            raise HTTPException(404, "This run is no longer in memory. Use the current report.")
        try:
            result = calculate(report["financial_candidates"], request, report["mode"])
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        report["financials"] = result
        report["memo_markdown"] = memo_markdown(report)
        return report
    finally:
        app.state.lock.release()


@app.post("/api/discover")
def discover_startups(request: DiscoverRequest):
    if request.mode == "live" and not request.confirm_live:
        raise HTTPException(403, "Confirm this bounded live sourcing run first.")
    if not app.state.lock.acquire(blocking=False):
        raise HTTPException(409, "Another operation is running. No discovery request was sent.")
    provider = None
    try:
        provider = LiveDiscovery() if request.mode == "live" else OfflineDiscovery()
        return discover(request.mandate, provider, request.mode)
    except RunError as exc:
        return JSONResponse({"detail": str(exc), "usage": provider.usage() if provider else None}, status_code=422)
    except Exception:
        return JSONResponse({"detail": "Discovery failed validation or received an unexpected provider response. No retry or company analysis was attempted.",
                             "usage": provider.usage() if provider else None}, status_code=502)
    finally:
        app.state.lock.release()


@app.get("/api/memo/{run_id}")
def memo(run_id: str):
    report = app.state.report
    if not report or report["run_id"] != run_id:
        raise HTTPException(404, "This report is no longer in memory.")
    return PlainTextResponse(report["memo_markdown"], headers={"Content-Disposition": 'attachment; filename="investment-memo.md"'})


app.mount("/static", StaticFiles(directory=STATIC), name="static")
