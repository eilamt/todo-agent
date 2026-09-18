"""Integration tests for the Flask GUI API — uses Flask test client."""
import json
import time
from unittest.mock import patch

import pytest

from todo_agent.core import store
from todo_agent.gui.server import app as flask_app


@pytest.fixture
def client(tmp_data_path, monkeypatch):
    monkeypatch.setattr(store, "get_data_file_path", lambda: tmp_data_path)
    monkeypatch.setattr(
        "todo_agent.config.get_data_file_path", lambda: tmp_data_path
    )
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        yield client


class TestGetData:
    def test_returns_empty_store(self, client):
        resp = client.get("/api/data")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["version"] == "1"
        assert data["lanes"] == []

    def test_returns_304_when_not_modified(self, client, tmp_data_path):
        # First request to get Last-Modified
        r1 = client.get("/api/data")
        lm = r1.headers.get("Last-Modified")
        assert lm is not None
        # Second request with If-Modified-Since
        r2 = client.get("/api/data", headers={"If-Modified-Since": lm})
        assert r2.status_code == 304


class TestCreateLane:
    def test_creates_lane(self, client):
        resp = client.post("/api/lanes", json={"name": "Work"})
        assert resp.status_code == 201
        assert resp.get_json()["name"] == "Work"

    def test_duplicate_returns_409(self, client):
        client.post("/api/lanes", json={"name": "Work"})
        resp = client.post("/api/lanes", json={"name": "Work"})
        assert resp.status_code == 409

    def test_missing_name_returns_400(self, client):
        resp = client.post("/api/lanes", json={})
        assert resp.status_code == 400


class TestDeleteLane:
    def test_deletes_lane_returns_counts(self, client):
        r = client.post("/api/lanes", json={"name": "Work"})
        lane_id = r.get_json()["id"]
        r2 = client.post(f"/api/lanes/{lane_id}/projects", json={"name": "P"})
        resp = client.delete(f"/api/lanes/{lane_id}")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["deleted"]["projects_deleted"] == 1

    def test_not_found_returns_404(self, client):
        resp = client.delete("/api/lanes/nonexistent-id")
        assert resp.status_code == 404


class TestItemPatch:
    def _setup(self, client):
        r = client.post("/api/lanes", json={"name": "Work"})
        lane_id = r.get_json()["id"]
        r2 = client.post(f"/api/lanes/{lane_id}/projects", json={"name": "P"})
        proj_id = r2.get_json()["id"]
        r3 = client.post(f"/api/projects/{proj_id}/items", json={"title": "T"})
        item_id = r3.get_json()["id"]
        return proj_id, item_id

    def test_status_update_returns_percent_complete(self, client):
        proj_id, item_id = self._setup(client)
        resp = client.patch(f"/api/items/{item_id}", json={"status": "completed"})
        assert resp.status_code == 200
        body = resp.get_json()
        assert "project_percent_complete" in body
        assert body["project_percent_complete"] == 100

    def test_delete_item_returns_percent_complete(self, client):
        proj_id, item_id = self._setup(client)
        resp = client.delete(f"/api/items/{item_id}")
        assert resp.status_code == 200
        body = resp.get_json()
        assert "project_percent_complete" in body
        assert body["project_percent_complete"] is None  # back to null after last item removed
