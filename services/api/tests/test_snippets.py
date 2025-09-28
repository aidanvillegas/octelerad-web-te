"""Integration tests for snippet CRUD, import/export, and delta sync."""

import io
import json
from datetime import datetime, timedelta

from fastapi.testclient import TestClient


def authenticate(client: TestClient) -> str:
    response = client.post("/auth/magic", json={"email": "test@example.com"})
    assert response.status_code == 200
    data = response.json()
    return data.get("access_token") or data.get("dev_token")


def test_snippet_flow(client: TestClient) -> None:
    token = authenticate(client)
    headers = {"Authorization": f"Bearer {token}"}

    create_payload = {
        "name": "Welcome Email",
        "trigger": "welc",
        "body": "Hello {{name}}",
        "tags": ["email"],
        "variables": {"name": ""},
    }

    create_resp = client.post("/workspaces/1/snippets", headers=headers, json=create_payload)
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["trigger"] == "welc"
    assert created["version"] == 1

    list_resp = client.get("/workspaces/1/snippets", headers=headers)
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert len(items) == 1
    assert items[0]["name"] == "Welcome Email"

    update_payload = {**create_payload, "body": "Updated body"}
    update_resp = client.put(
        f"/workspaces/1/snippets/{created['id']}", headers=headers, json=update_payload
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["version"] == 2
    assert updated["body"] == "Updated body"

    restore_resp = client.post(
        f"/workspaces/1/snippets/{created['id']}/restore/1", headers=headers
    )
    assert restore_resp.status_code == 200
    restored = restore_resp.json()
    assert restored["version"] == 3
    assert restored["body"] == "Hello {{name}}"

    export_resp = client.get("/workspaces/1/export", headers=headers)
    assert export_resp.status_code == 200
    export_data = export_resp.json()
    assert export_data["schema"] == "text-expander.v1"
    assert export_data["workspace_id"] == 1
    assert len(export_data["snippets"]) == 1

    import_payload = {
        "schema": "text-expander.v1",
        "snippets": [
            {
                "name": "Follow Up",
                "trigger": "follow",
                "body": "Thanks again",
                "tags": ["email"],
                "variables": {"name": ""},
            }
        ],
    }
    file = io.BytesIO(json.dumps(import_payload).encode("utf-8"))
    import_resp = client.post(
        "/workspaces/1/import",
        headers=headers,
        files={"file": ("import.json", file, "application/json")},
    )
    assert import_resp.status_code == 200
    assert import_resp.json()["imported"] == 1

    list_after_import = client.get("/workspaces/1/snippets", headers=headers).json()
    triggers = sorted(snippet["trigger"] for snippet in list_after_import)
    assert triggers == ["follow", "welc"]

    historical_ts = (datetime.utcnow() - timedelta(minutes=1)).isoformat() + "Z"
    delta_resp = client.get(
        f"/workspaces/1/snippets/since?since_ts={historical_ts}", headers=headers
    )
    assert delta_resp.status_code == 200
    delta_items = delta_resp.json()
    assert len(delta_items) == 2

    audit_resp = client.get("/workspaces/1/audit", headers=headers)
    assert audit_resp.status_code == 200
    actions = {entry["action"] for entry in audit_resp.json()}
    expected_actions = {"create_snippet", "update_snippet", "restore_version", "export", "import"}
    assert expected_actions.issubset(actions)


def test_metrics_endpoint(client: TestClient) -> None:
    response = client.get("/metrics")
    assert response.status_code == 200
    body = response.text
    assert "macro_http_requests_total" in body
