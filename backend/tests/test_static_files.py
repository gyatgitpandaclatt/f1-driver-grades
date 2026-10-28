import pytest
from fastapi.testclient import TestClient

import app.main as main

if not main.FRONTEND_DIST.is_dir():
    pytest.skip("frontend/dist not built; the static route isn't mounted", allow_module_level=True)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(main, "_warm_caches", lambda: None)
    return TestClient(main.app)


@pytest.mark.parametrize("path", [
    "/..%2f..%2fbackend%2frequirements.txt",
    "/%2e%2e/%2e%2e/backend/requirements.txt",
    "/..%2F..%2FREADME.md",
])
def test_paths_outside_dist_get_the_app_not_the_file(client, path):
    r = client.get(path)
    assert r.status_code == 200
    assert r.text.lstrip().lower().startswith("<!doctype html")


def test_files_inside_dist_are_still_served(client):
    assert client.get("/index.html").text.lstrip().lower().startswith("<!doctype html")
