import json
import sys
import time
from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, Response

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))


class ActivityLog:
    def __init__(self, max_entries=2000):
        self.max_entries = max_entries
        self._entries = deque(maxlen=max_entries)

    def add(self, level, kind, detail, meta=None):
        eid = f"{time.time():.6f}.{uuid4().hex[:6]}"
        self._entries.append(
            {
                "id": eid,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
                "level": level.upper(),
                "kind": kind,
                "detail": detail,
                "meta": meta or {},
            }
        )
        return eid

    def info(self, kind, detail, **meta):
        return self.add("INFO", kind, detail, meta)

    def warn(self, kind, detail, **meta):
        return self.add("WARNING", kind, detail, meta)

    def error(self, kind, detail, **meta):
        return self.add("ERROR", kind, detail, meta)

    def query(self, limit=50, offset=0, level=None, kind=None, search=None, sort="desc", after_id=None):
        entries = list(self._entries)
        if after_id:
            try:
                at = float(after_id.split(".")[0])
                entries = [e for e in entries if float(e["id"].split(".")[0]) > at]
            except:
                pass
        if level:
            lo = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}
            ml = lo.get(level.upper(), 1)
            entries = [e for e in entries if lo.get(e["level"], 1) >= ml]
        if kind:
            entries = [e for e in entries if e["kind"] == kind]
        if search:
            q = search.lower()
            entries = [e for e in entries if q in e["detail"].lower()]
        entries.sort(key=lambda e: e["id"], reverse=(sort == "desc"))
        total = len(entries)
        page = entries[offset : offset + limit]
        return {
            "entries": page,
            "total": total,
            "limit": limit,
            "offset": offset,
            "max_entries": self.max_entries,
            "sort": sort,
        }

    def stats(self):
        levels, kinds = {}, {}
        for e in self._entries:
            levels[e["level"]] = levels.get(e["level"], 0) + 1
            kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
        return {"total": len(self._entries), "max_entries": self.max_entries, "levels": levels, "kinds": kinds}

    def export(self, format="json", **filters):
        result = self.query(limit=self.max_entries, **filters)
        if format == "csv":
            import csv
            import io

            buf = io.StringIO()
            w = csv.writer(buf)
            w.writerow(["id", "timestamp", "level", "kind", "detail", "meta"])
            for e in result["entries"]:
                w.writerow([e["id"], e["timestamp"], e["level"], e["kind"], e["detail"], json.dumps(e["meta"])])
            return buf.getvalue()
        return json.dumps(result["entries"], indent=2)

    def clear(self):
        self._entries.clear()


al = ActivityLog()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.activity_log = al
    al.info("server", "Server started")
    yield


app = FastAPI(title="PyWinAuto MCP", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
@app.get("/api/health")
async def health():
    return {"status": "ok", "server": "PyWinAuto MCP", "version": "0.1.0"}


@app.get("/api/logs")
async def get_logs(
    request: Request, limit=50, offset=0, level=None, kind=None, search=None, sort="desc", after_id=None
):
    log = getattr(request.app.state, "activity_log", None)
    if not log:
        return {"entries": [], "total": 0, "limit": limit, "offset": offset, "max_entries": 0, "sort": sort}
    return log.query(limit=limit, offset=offset, level=level, kind=kind, search=search, sort=sort, after_id=after_id)


@app.get("/api/logs/stats")
async def logs_stats(request: Request):
    log = getattr(request.app.state, "activity_log", None)
    if not log:
        return {"total": 0, "max_entries": 0, "levels": {}, "kinds": {}}
    return log.stats()


@app.get("/api/logs/export")
async def logs_export(request: Request, format="json", level=None, kind=None, search=None):
    log = getattr(request.app.state, "activity_log", None)
    if not log:
        return PlainTextResponse("[]", media_type="application/json")
    content = log.export(format=format, level=level, kind=kind, search=search)
    media = "text/csv" if format == "csv" else "application/json"
    return Response(
        content=content, media_type=media, headers={"Content-Disposition": f'attachment; filename="logs.{format}"'}
    )


@app.delete("/api/logs")
async def clear_logs(request: Request):
    log = getattr(request.app.state, "activity_log", None)
    if log:
        log.clear()
    return {"success": True, "message": "Logs cleared."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
