"""QR intake-link endpoint tests: auth required, PNG bytes, expected URLs."""

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
BASE = "https://sadot.lavit.io"


def test_qr_endpoints_require_auth(client):
    assert client.get("/api/v1/qr/links").status_code == 401
    assert client.get("/api/v1/qr/surrender.png").status_code == 401
    assert client.get("/api/v1/qr/adopt.png").status_code == 401


def test_qr_links_returns_expected_urls(client, auth):
    r = client.get("/api/v1/qr/links", headers=auth)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["surrender"] == f"{BASE}/surrender?src=qr"
    assert body["adopt"] == f"{BASE}/adopt?src=qr"


def test_qr_links_deep_links_dog(client, auth):
    r = client.get("/api/v1/qr/links", params={"dog_id": 5}, headers=auth)
    assert r.status_code == 200, r.text
    assert r.json()["adopt"] == f"{BASE}/adopt?src=qr&dog_id=5"


def test_qr_surrender_png(client, auth):
    r = client.get("/api/v1/qr/surrender.png", headers=auth)
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "image/png"
    assert r.content.startswith(PNG_MAGIC)
    assert len(r.content) > 0


def test_qr_adopt_png(client, auth):
    r = client.get("/api/v1/qr/adopt.png", headers=auth)
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "image/png"
    assert r.content.startswith(PNG_MAGIC)
    assert len(r.content) > 0


def test_qr_adopt_png_with_dog_id(client, auth):
    r = client.get("/api/v1/qr/adopt.png", params={"dog_id": 12}, headers=auth)
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "image/png"
    assert r.content.startswith(PNG_MAGIC)
