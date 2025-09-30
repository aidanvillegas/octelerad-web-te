"""FastAPI entrypoint for the public datasets API."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes_datasets import router as datasets_router
from .ws import ws_router

app = FastAPI(title='Public Dataset API', version='0.4.0', docs_url='/docs')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/healthz', tags=['meta'])
def healthz() -> dict[str, str]:
    return {'status': 'ok'}


app.include_router(datasets_router)
app.include_router(ws_router)
