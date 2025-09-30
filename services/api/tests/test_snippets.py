"""Integration tests for the public dataset API."""

from __future__ import annotations

import io

from fastapi.testclient import TestClient

from services.api.app import models_datasets  # ensure models are imported


def test_dataset_crud_flow(client: TestClient) -> None:
    create_payload = {"name": "Test Dataset", "created_by_client": "test-browser", "columns": ["Column A"]}
    response = client.post("/datasets", json=create_payload)
    assert response.status_code == 201
    dataset = response.json()
    dataset_id = dataset["id"]

    response = client.get("/datasets/all")
    assert response.status_code == 200
    assert any(item["id"] == dataset_id for item in response.json()["all"])

    response = client.get("/datasets/mine-local", params={"client_id": "test-browser"})
    assert response.status_code == 200
    assert any(item["id"] == dataset_id for item in response.json())

    response = client.get(f"/datasets/{dataset_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Dataset"

    response = client.get(f"/datasets/{dataset_id}/rows")
    assert response.status_code == 200
    assert response.json() == {"total": 0, "rows": []}

    upsert_payload = {"rows": [{"Column A": ""}]}
    response = client.post(f"/datasets/{dataset_id}/rows/upsert", json=upsert_payload)
    assert response.status_code == 200
    assert response.json()["created"] == 1

    response = client.get(f"/datasets/{dataset_id}/rows")
    data = response.json()
    assert data["total"] == 1
    row_id = data["rows"][0]["id"]

    patch_payload = {"id": row_id, "key": "Column A", "value": "Updated"}
    response = client.post(f"/datasets/{dataset_id}/rows/patch", json=patch_payload)
    assert response.status_code == 200
    response = client.get(f"/datasets/{dataset_id}/rows")
    assert response.json()["rows"][0]["Column A"] == "Updated"

    response = client.post(f"/datasets/{dataset_id}/columns/add", json={"key": "Column B"})
    assert response.status_code == 200
    response = client.get(f"/datasets/{dataset_id}")
    assert any(col["key"] == "Column B" for col in response.json()["schema"]["columns"])

    response = client.delete(f"/datasets/{dataset_id}/rows", params={"ids": row_id})
    assert response.status_code == 200
    assert response.json()["deleted"] == 1

    response = client.get(f"/datasets/{dataset_id}/export", params={"fmt": "json"})
    assert response.status_code == 200
    export_payload = response.json()
    assert export_payload["filename"].endswith(".json")


def test_import_csv(client: TestClient) -> None:
    create = client.post("/datasets", json={"name": "Import", "created_by_client": None, "columns": ["Column A", "Column B"]})
    assert create.status_code == 201
    dataset_id = create.json()["id"]

    csv_content = """Column A,Column B
1,2
3,4
"""
    files = {"file": ("data.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    response = client.post(f"/datasets/{dataset_id}/import", files=files)
    assert response.status_code == 200
    assert response.json()["rows_added"] == 2

    response = client.get(f"/datasets/{dataset_id}/rows")
    data = response.json()
    assert data["total"] == 2
    assert any(row["Column A"] == "1" for row in data["rows"])

    response = client.get(f"/datasets/{dataset_id}/export", params={"fmt": "csv"})
    assert response.status_code == 200
    export_payload = response.json()
    assert export_payload["filename"].endswith(".csv")
