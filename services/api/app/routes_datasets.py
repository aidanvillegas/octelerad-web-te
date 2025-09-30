"""Public dataset endpoints with realtime collaboration hooks."""

from __future__ import annotations

import csv
import io
import json
import os
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import func, String
from sqlalchemy.orm import Session

from .database import get_db
from .models import AuditLog
from .models_datasets import Dataset, DatasetRow
from .realtime import hub

router = APIRouter(prefix='/datasets', tags=['datasets'])

logger = logging.getLogger(__name__)


MAX_IMPORT_BYTES = int(os.getenv('MAX_IMPORT_BYTES', 5 * 1024 * 1024))

DEFAULT_COLUMNS = [
    'KKC CODE',
    'CHAPTER',
    'BODY PART',
    'MODALITTY',
    'OCTR UI',
    'DX',
    'DZ',
    'DZ PRIOR',
    'AGE CODE',
    'SEX',
    'DZ',
    'IMPRESSION',
    'LOG COMPLETE',
]


def _schema_from_columns(columns: List[str]) -> Dict[str, Any]:
    return {'columns': [{'key': col, 'type': 'string'} for col in columns]}


def _dataset_summary(dataset: Dataset) -> Dict[str, Any]:
    return {
        'id': dataset.id,
        'name': dataset.name,
        'updated_at': dataset.updated_at.isoformat() + 'Z',
    }


@router.get('/all')
def list_all(db: Session = Depends(get_db)) -> Dict[str, List[Dict[str, Any]]]:
    datasets = db.query(Dataset).order_by(Dataset.updated_at.desc()).all()
    return {'all': [_dataset_summary(ds) for ds in datasets]}


@router.get('/mine-local')
def list_mine_local(client_id: str = Query(..., description='Anonymous client identifier'), db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    datasets = (
        db.query(Dataset)
        .filter(Dataset.created_by_client == client_id)
        .order_by(Dataset.updated_at.desc())
        .all()
    )
    return [_dataset_summary(ds) for ds in datasets]


class DatasetCreate(BaseModel):
    name: str = Field(..., max_length=255)
    columns: Optional[List[str]] = None
    created_by_client: Optional[str] = None


@router.post('', status_code=201)
def create_dataset(payload: DatasetCreate, db: Session = Depends(get_db)) -> Dict[str, Any]:
    name = (payload.name or '').strip()
    if not name:
        raise HTTPException(status_code=400, detail='Dataset name required')

    raw_columns = payload.columns or DEFAULT_COLUMNS
    if not isinstance(raw_columns, list) or not all(isinstance(col, str) for col in raw_columns):
        raise HTTPException(status_code=400, detail='Invalid columns')

    columns = [col.strip() for col in raw_columns if isinstance(col, str) and col.strip()]
    if not columns:
        columns = list(DEFAULT_COLUMNS)

    schema = {'columns': [{'key': col, 'type': 'string'} for col in columns]}

    dataset = Dataset(name=name, schema=schema, created_by_client=payload.created_by_client)
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    try:
        db.add(
            AuditLog(
                workspace_id=None,
                user_id=None,
                action='create_dataset',
                meta={'dataset_id': dataset.id},
            )
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.exception(
            'dataset_create_audit_failed',
            extra={'dataset_id': dataset.id, 'error': str(exc)},
        )

    return {
        'id': dataset.id,
        'name': dataset.name,
        'schema': dataset.schema,
        'updated_at': dataset.updated_at.isoformat() + 'Z',
    }


@router.get('/{dataset_id}')
def get_dataset(dataset_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail='Dataset not found')
    return {
        'id': dataset.id,
        'name': dataset.name,
        'schema': dataset.schema,
        'updated_at': dataset.updated_at.isoformat() + 'Z',
    }


@router.get('/{dataset_id}/rows')
def list_rows(
    dataset_id: int,
    q: Optional[str] = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=500, ge=1, le=2000),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail='Dataset not found')

    query = db.query(DatasetRow).filter(
        DatasetRow.dataset_id == dataset_id,
        DatasetRow.archived.is_(False),
    )
    if q:
        like = f'%{q}%'
        query = query.filter(func.cast(DatasetRow.data, String).ilike(like))

    total = query.count()
    rows = (
        query.order_by(DatasetRow.id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    payload = [{**row.data, 'id': row.id} for row in rows]
    return {'total': total, 'rows': payload}


class CellPatch(BaseModel):
    id: int
    key: str
    value: Any


@router.post('/{dataset_id}/rows/patch')
async def patch_cell(
    dataset_id: int,
    payload: CellPatch,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    row = (
        db.query(DatasetRow)
        .filter(
            DatasetRow.dataset_id == dataset_id,
            DatasetRow.id == payload.id,
            DatasetRow.archived.is_(False),
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail='Row not found')

    data = dict(row.data)
    data[payload.key] = payload.value
    row.data = data
    db.commit()

    message = {
        'type': 'cell',
        'row_id': row.id,
        'key': payload.key,
        'value': payload.value,
        'updated_at': datetime.utcnow().isoformat() + 'Z',
    }
    background.add_task(hub.broadcast, dataset_id, message)
    return {'ok': True, 'applied': message}


class RowUpsert(BaseModel):
    rows: List[Dict[str, Any]]


@router.post('/{dataset_id}/rows/upsert')
async def upsert_rows(
    dataset_id: int,
    payload: RowUpsert,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail='Dataset not found')

    created_rows: List[Dict[str, Any]] = []
    for item in payload.rows:
        row_id = item.get('id')
        data = {k: v for k, v in item.items() if k != 'id'}
        if row_id:
            row = (
                db.query(DatasetRow)
                .filter(DatasetRow.id == row_id, DatasetRow.dataset_id == dataset_id)
                .first()
            )
            if row:
                row.data = data
        else:
            row = DatasetRow(dataset_id=dataset_id, data=data)
            db.add(row)
            db.flush()
            created_rows.append({**row.data, 'id': row.id})
    db.commit()

    if created_rows:
        background.add_task(hub.broadcast, dataset_id, {'type': 'rows_upsert', 'rows': created_rows})

    return {'created': len(created_rows)}


class ColumnAdd(BaseModel):
    key: str


@router.post('/{dataset_id}/columns/add')
async def add_column(
    dataset_id: int,
    payload: ColumnAdd,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail='Dataset not found')

    key = payload.key.strip()
    if not key:
        raise HTTPException(status_code=400, detail='Column key required')

    columns = list(dataset.schema.get('columns', []))

    if any(col.get('key') == key for col in columns):
        raise HTTPException(status_code=409, detail='Column already exists')

    columns.append({'key': key, 'type': 'string'})
    dataset.schema = {'columns': columns}
    db.commit()

    background.add_task(hub.broadcast, dataset_id, {'type': 'column_add', 'key': key})
    return {'schema': dataset.schema}


@router.delete('/{dataset_id}/rows')
async def delete_rows(
    dataset_id: int,
    ids: List[int] = Query(..., description='Row IDs to archive'),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    rows = (
        db.query(DatasetRow)
        .filter(DatasetRow.dataset_id == dataset_id, DatasetRow.id.in_(ids))
        .all()
    )
    if not rows:
        return {'deleted': 0}

    for row in rows:
        row.archived = True
    db.commit()

    await hub.broadcast(dataset_id, {'type': 'delete_rows', 'ids': ids})
    return {'deleted': len(rows)}


@router.post('/{dataset_id}/import')
async def import_dataset(
    dataset_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail='Dataset not found')

    raw = file.file.read()
    if not raw:
        raise HTTPException(status_code=400, detail='Empty file')
    if len(raw) > MAX_IMPORT_BYTES:
        raise HTTPException(status_code=413, detail='Import too large')

    filename = (file.filename or '').lower()

    rows_to_add: List[Dict[str, Any]] = []
    detected_columns: List[str] = []

    try:
        if filename.endswith('.json'):
            data = json.loads(raw.decode('utf-8'))
            if isinstance(data, dict) and isinstance(data.get('rows'), list):
                rows_to_add = data['rows']
            elif isinstance(data, list):
                rows_to_add = data
            if rows_to_add:
                keys = set()
                for row in rows_to_add:
                    keys.update(row.keys())
                detected_columns = sorted(keys)
        else:
            text_content = raw.decode('utf-8', errors='replace')
            reader = csv.DictReader(io.StringIO(text_content))
            detected_columns = reader.fieldnames or []
            for row in reader:
                rows_to_add.append(dict(row))
    except Exception as exc:
        logger.exception("import_dataset_failed", extra={'dataset_id': dataset_id})
        raise HTTPException(status_code=400, detail='Failed to parse import file') from exc

    if detected_columns:
        dataset.schema = _schema_from_columns(detected_columns)

    created_rows: List[Dict[str, Any]] = []
    if rows_to_add:
        for row in rows_to_add:
            dataset_row = DatasetRow(dataset_id=dataset_id, data=row)
            db.add(dataset_row)
            db.flush()
            created_rows.append({**dataset_row.data, 'id': dataset_row.id})
    db.commit()

    if created_rows:
        await hub.broadcast(dataset_id, {'type': 'rows_upsert', 'rows': created_rows})

    return {'status': 'ok', 'rows_added': len(created_rows), 'schema': dataset.schema}


@router.get('/{dataset_id}/export')
def export_dataset(
    dataset_id: int,
    fmt: str = Query(default='json', pattern='^(json|csv)$'),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail='Dataset not found')

    rows = db.query(DatasetRow).filter(
        DatasetRow.dataset_id == dataset_id,
        DatasetRow.archived.is_(False),
    ).all()

    if fmt == 'csv':
        output = io.StringIO()
        headers = [col['key'] for col in dataset.schema.get('columns', [])]
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.data.get(key, '') for key in headers})
        return {'filename': f'{dataset.name}.csv', 'content': output.getvalue()}

    payload = [{**row.data, 'id': row.id} for row in rows]
    return {'filename': f'{dataset.name}.json', 'content': payload}
