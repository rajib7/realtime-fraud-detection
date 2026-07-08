"""Download router.

Exposes the assignment deliverables under /api/download/<name>. Explicitly
sets Content-Disposition: attachment so browsers always save the file
instead of trying to render it inline, and works through the /api/*
ingress path (which some hosts route more permissively than static /*).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse


router = APIRouter(prefix="/download", tags=["download"])


# Filename -> (absolute source path, MIME type, human filename)
_FRONTEND_PUBLIC = Path(__file__).resolve().parent.parent.parent / "frontend" / "public"

_ASSETS: Dict[str, Dict[str, str]] = {
    "source.tar.gz": {
        "path": str(_FRONTEND_PUBLIC / "fraudops-submission.tar.gz"),
        "mime": "application/gzip",
        "filename": "fraudops-submission.tar.gz",
    },
    "source.zip": {
        "path": str(_FRONTEND_PUBLIC / "fraudops-submission.zip"),
        "mime": "application/zip",
        "filename": "fraudops-submission.zip",
    },
    "demo-video.webm": {
        "path": str(_FRONTEND_PUBLIC / "demo-video.webm"),
        "mime": "video/webm",
        "filename": "fraudops-demo.webm",
    },
    "screenshots.zip": {
        "path": str(_FRONTEND_PUBLIC / "demo-screenshots.zip"),
        "mime": "application/zip",
        "filename": "fraudops-demo-screenshots.zip",
    },
    "presentation.pptx": {
        "path": str(_FRONTEND_PUBLIC / "fraudops-presentation.pptx"),
        "mime": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "filename": "fraudops-presentation.pptx",
    },
    "presentation.pdf": {
        "path": str(_FRONTEND_PUBLIC / "fraudops-presentation.pdf"),
        "mime": "application/pdf",
        "filename": "fraudops-presentation.pdf",
    },
}


@router.get("")
async def list_downloads() -> Dict[str, Dict[str, object]]:
    out: Dict[str, Dict[str, object]] = {}
    for key, info in _ASSETS.items():
        p = Path(info["path"])
        out[key] = {
            "url": f"/api/download/{key}",
            "filename": info["filename"],
            "mime": info["mime"],
            "size_bytes": p.stat().st_size if p.exists() else 0,
            "available": p.exists(),
        }
    return out


@router.get("/{name}")
async def download(name: str):
    if name not in _ASSETS:
        raise HTTPException(status_code=404, detail=f"Unknown asset: {name}")
    info = _ASSETS[name]
    path = Path(info["path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Asset not built yet: {name}")
    return FileResponse(
        path=str(path),
        media_type=info["mime"],
        filename=info["filename"],
        headers={
            "Content-Disposition": f'attachment; filename="{info["filename"]}"',
            "Cache-Control": "no-store",
        },
    )
